# -*- coding: utf-8 -*-

# AwesomeTTS text-to-speech add-on for Anki
#
# Copyright (C) 2010-2014  Anki AwesomeTTS Development Team
# Copyright (C) 2010-2012  Arthur Helfstein Fragoso
# Copyright (C) 2013-2014  Dave Shifflett
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Configuration dialog"""

__all__ = ['Configurator']

from locale import format as locale
import os
import os.path
from sys import platform

from PyQt4 import QtCore, QtGui

from .base import Dialog, ServiceDialog
from .common import Checkbox, Label, Note
from .common import key_event_combo, key_combo_desc
from .listviews import SubListView as _SubListView

# all methods might need 'self' in the future, pylint:disable=R0201


class Configurator(Dialog):
    """Provides a dialog for configuring the add-on."""

    _PROPERTY_KEYS = [
        'automatic_answers', 'automatic_answers_errors', 'automatic_questions',
        'automatic_questions_errors', 'debug_file', 'debug_stdout',
        'delay_answers_onthefly', 'delay_answers_stored_ours',
        'delay_answers_stored_theirs', 'delay_questions_onthefly',
        'delay_questions_stored_ours', 'delay_questions_stored_theirs',
        'lame_flags', 'launch_browser_generator', 'launch_browser_stripper',
        'launch_configurator', 'launch_editor_generator', 'launch_templater',
        'otf_only_revealed_cloze', 'otf_remove_hints', 'spec_note_strip',
        'spec_note_ellipsize', 'spec_template_ellipsize', 'spec_note_count',
        'spec_note_count_wrap', 'spec_template_count',
        'spec_template_count_wrap', 'spec_template_strip', 'strip_note_braces',
        'strip_note_brackets', 'strip_note_parens', 'strip_template_braces',
        'strip_template_brackets', 'strip_template_parens', 'sub_note_cloze',
        'sub_template_cloze', 'sul_note', 'sul_template', 'throttle_sleep',
        'throttle_threshold', 'tts_key_a', 'tts_key_q', 'updates_enabled',
    ]

    _PROPERTY_WIDGETS = (Checkbox, QtGui.QComboBox, QtGui.QLineEdit,
                         QtGui.QPushButton, QtGui.QSpinBox, QtGui.QListView)

    __slots__ = ['_alerts', '_ask', '_preset_editor', '_sul_compiler']

    def __init__(self, alerts, ask, sul_compiler, *args, **kwargs):
        self._alerts = alerts
        self._ask = ask
        self._preset_editor = None
        self._sul_compiler = sul_compiler

        super(Configurator, self).__init__(title="Configuration",
                                           *args, **kwargs)

    # UI Construction ########################################################

    def _ui(self):
        """Returns vertical layout w/ banner, our tabs, cancel/OK."""

        layout = super(Configurator, self)._ui()
        layout.addWidget(self._ui_tabs())
        layout.addWidget(self._ui_buttons())
        return layout

    def _ui_tabs(self):
        """Returns tab widget w/ Playback, Text, MP3s, Advanced."""

        use_icons = not platform.startswith('darwin')
        tabs = QtGui.QTabWidget()

        for content, icon, label in [
                (self._ui_tabs_playback, 'player-time', "Playback"),
                (self._ui_tabs_text, 'editclear', "Text"),
                (self._ui_tabs_mp3gen, 'document-new', "MP3s"),
                (self._ui_tabs_windows, 'kpersonalizer', "Windows"),
                (self._ui_tabs_advanced, 'configure', "Advanced"),
        ]:
            if use_icons:
                tabs.addTab(content(), QtGui.QIcon(':/icons/%s.png' % icon),
                            label)
            else:  # active tabs do not display correctly on Mac OS X w/ icons
                tabs.addTab(content(), label)

        tabs.currentChanged.connect(lambda: (tabs.adjustSize(),
                                             self.adjustSize()))
        return tabs

    def _ui_tabs_playback(self):
        """Returns the "Playback" tab."""

        vert = QtGui.QVBoxLayout()
        vert.addWidget(self._ui_tabs_playback_group(
            'automatic_questions', 'tts_key_q',
            'delay_questions_', "Questions / Fronts of Cards",
        ))
        vert.addWidget(self._ui_tabs_playback_group(
            'automatic_answers', 'tts_key_a',
            'delay_answers_', "Answers / Backs of Cards",
        ))
        vert.addSpacing(self._SPACING)
        vert.addWidget(Label('Anki controls if and how to play [sound] '
                             'tags. See "Help" for more information.'))
        vert.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(vert)
        return tab

    def _ui_tabs_playback_group(self, automatic_key, shortcut_key,
                                delay_key_prefix, label):
        """
        Returns the "Questions / Fronts of Cards" and "Answers / Backs
        of Cards" input groups.
        """

        hor = QtGui.QHBoxLayout()
        automatic = Checkbox("Automatically play on-the-fly <tts> tags",
                             automatic_key)
        errors = Checkbox("Show errors", automatic_key + '_errors')
        hor.addWidget(automatic)
        hor.addWidget(errors)
        hor.addStretch()

        layout = QtGui.QVBoxLayout()
        layout.addLayout(hor)

        wait_widgets = {}
        for subkey, desc in [('onthefly', "on-the-fly <tts> tags"),
                             ('stored_ours', "AwesomeTTS [sound] tags"),
                             ('stored_theirs', "other [sound] tags")]:
            spinner = QtGui.QSpinBox()
            spinner.setObjectName(delay_key_prefix + subkey)
            spinner.setRange(0, 30)
            spinner.setSingleStep(1)
            spinner.setSuffix(" seconds")
            wait_widgets[subkey] = spinner

            hor = QtGui.QHBoxLayout()
            hor.addWidget(Label("Wait"))
            hor.addWidget(spinner)
            hor.addWidget(Label("before automatically playing " + desc))
            hor.addStretch()
            layout.addLayout(hor)

        automatic.stateChanged.connect(lambda enabled: (
            errors.setEnabled(enabled),
            wait_widgets['onthefly'].setEnabled(enabled),
        ))

        hor = QtGui.QHBoxLayout()
        hor.addWidget(Label("To manually play on-the-fly <tts> tags, strike"))
        hor.addWidget(self._factory_shortcut(shortcut_key))
        hor.addStretch()
        layout.addLayout(hor)

        group = QtGui.QGroupBox(label)
        group.setLayout(layout)
        return group

    def _ui_tabs_text(self):
        """Returns the "Text" tab."""

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._ui_tabs_text_mode(
            '_template_',
            "Handling Template Text (e.g. On-the-Fly, Context Menus)",
            "For a front-side rendered cloze,",
            [('anki', "read however Anki displayed it"),
             ('wrap', "read w/ hint wrapped in ellipses"),
             ('ellipsize', "read as an ellipsis, ignoring hint"),
             ('remove', "remove entirely")],
            template_options=True,
        ), 50)
        layout.addWidget(self._ui_tabs_text_mode(
            '_note_',
            "Handling Text from a Note Field (e.g. Browser Generator)",
            "For a braced cloze marker,",
            [('anki', "read as Anki would display on a card front"),
             ('wrap', "replace w/ hint wrapped in ellipses"),
             ('deleted', "replace w/ deleted text"),
             ('ellipsize', "replace w/ ellipsis, ignoring both"),
             ('remove', "remove entirely")],
        ), 50)

        tab = QtGui.QWidget()
        tab.setLayout(layout)
        return tab

    def _ui_tabs_text_mode(self, infix, label, *args, **kwargs):
        """Returns group box for the given text manipulation context."""

        subtabs = QtGui.QTabWidget()
        subtabs.setTabPosition(QtGui.QTabWidget.West)

        for sublabel, sublayout in [
                ("Simple", self._ui_tabs_text_mode_simple(infix, *args,
                                                          **kwargs)),
                ("Advanced", self._ui_tabs_text_mode_adv(infix)),
        ]:
            subwidget = QtGui.QWidget()
            subwidget.setLayout(sublayout)
            subtabs.addTab(subwidget, sublabel)

        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(subtabs)

        group = QtGui.QGroupBox(label)
        group.setFlat(True)
        group.setLayout(layout)

        _, top, right, bottom = layout.getContentsMargins()
        layout.setContentsMargins(0, top, right, bottom)
        _, top, right, bottom = group.getContentsMargins()
        group.setContentsMargins(0, top, right, bottom)
        return group

    def _ui_tabs_text_mode_simple(self, infix, cloze_description,
                                  cloze_options, template_options=False):
        """
        Returns a layout with the "simple" configuration options
        available for manipulating text from the given context.
        """

        select = QtGui.QComboBox()
        for option_value, option_text in cloze_options:
            select.addItem(option_text, option_value)
        select.setObjectName(infix.join(['sub', 'cloze']))

        hor = QtGui.QHBoxLayout()
        hor.addWidget(Label(cloze_description))
        hor.addWidget(select)
        hor.addStretch()

        layout = QtGui.QVBoxLayout()
        layout.addLayout(hor)

        if template_options:
            hor = QtGui.QHBoxLayout()
            hor.addWidget(Checkbox("For cloze answers, read revealed text "
                                   "only", 'otf_only_revealed_cloze'))
            hor.addWidget(Checkbox("Ignore {{hint}} fields",
                                   'otf_remove_hints'))
            layout.addLayout(hor)

        hor = QtGui.QHBoxLayout()
        hor.addWidget(Label("Strip off text within:"))
        for option_subkey, option_label in [('parens', "parentheses"),
                                            ('brackets', "brackets"),
                                            ('braces', "braces")]:
            hor.addWidget(Checkbox(option_label,
                                   infix.join(['strip', option_subkey])))
        hor.addStretch()

        layout.addLayout(hor)
        layout.addLayout(self._ui_tabs_text_mode_simple_spec(
            infix, 'strip', ("Remove all", "characters from the input")))
        layout.addLayout(self._ui_tabs_text_mode_simple_spec(
            infix, 'count', ("Count adjacent", "characters"), True))
        layout.addLayout(self._ui_tabs_text_mode_simple_spec(
            infix, 'ellipsize', ("Replace", "characters with an ellipsis")))
        layout.addStretch()
        return layout

    def _ui_tabs_text_mode_simple_spec(self, infix, suffix, labels,
                                       wrap=False):
        """Returns a layout for specific character handling."""

        line_edit = QtGui.QLineEdit()
        line_edit.setObjectName(infix.join(['spec', suffix]))
        line_edit.setValidator(self._ui_tabs_text_mode_simple_spec.ucsv)
        line_edit.setFixedWidth(50)

        hor = QtGui.QHBoxLayout()
        hor.addWidget(Label(labels[0]))
        hor.addWidget(line_edit)
        hor.addWidget(Label(labels[1]))
        if wrap:
            hor.addWidget(Checkbox("wrap in ellipses",
                                   ''.join(['spec', infix, suffix, '_wrap'])))
        hor.addStretch()
        return hor

    class _UniqueCharacterStringValidator(QtGui.QValidator):
        """QValidator returning unique, sorted characters."""

        def fixup(self, original):
            """Returns unique characters from original, sorted."""

            return ''.join(sorted({c for c in original if not c.isspace()}))

        def validate(self, original, offset):  # pylint:disable=W0613
            """Fixes original text and resets cursor to end of line."""

            filtered = self.fixup(original)
            return QtGui.QValidator.Acceptable, filtered, len(filtered)

    _ui_tabs_text_mode_simple_spec.ucsv = _UniqueCharacterStringValidator()

    def _ui_tabs_text_mode_adv(self, infix):
        """
        Returns a layout with the "advanced" pattern replacement
        panel for manipulating text from the given context.
        """

        buttons = []
        for tooltip, icon in [("Add New Rule", 'list-add'),
                              ("Move Selected Up", 'arrow-up'),
                              ("Move Selected Down", 'arrow-down'),
                              ("Remove Selected", 'editdelete')]:
            btn = QtGui.QPushButton(QtGui.QIcon(':/icons/%s.png' % icon), "")
            btn.setIconSize(QtCore.QSize(16, 16))
            btn.setFlat(True)
            btn.setToolTip(tooltip)
            buttons.append(btn)

        list_view = _SubListView(self._sul_compiler, buttons)
        list_view.setObjectName('sul' + infix.rstrip('_'))
        list_view.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                QtGui.QSizePolicy.Ignored)

        vert = QtGui.QVBoxLayout()
        for btn in buttons:
            vert.addWidget(btn)
        vert.insertStretch(len(buttons) - 1)

        hor = QtGui.QHBoxLayout()
        hor.addWidget(list_view)
        hor.addLayout(vert)
        return hor

    def _ui_tabs_mp3gen(self):
        """Returns the "MP3s" tab."""

        vert = QtGui.QVBoxLayout()
        vert.addWidget(Note("Note that AwesomeTTS no longer generates audio "
                            "filenames directly from input phrases. Instead, "
                            "these are based on a hash of the given inputs."))
        vert.addSpacing(self._SPACING)
        vert.addWidget(self._ui_tabs_mp3gen_lame())
        vert.addWidget(self._ui_tabs_mp3gen_throttle())
        vert.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(vert)
        return tab

    def _ui_tabs_mp3gen_lame(self):
        """Returns the "LAME Transcoder" input group."""

        flags = QtGui.QLineEdit()
        flags.setObjectName('lame_flags')
        flags.setPlaceholderText("e.g. '-q 5' for medium quality")

        rtr = self._addon.router
        vert = QtGui.QVBoxLayout()
        vert.addWidget(Note("Specify flags passed to lame when making MP3s."))
        vert.addWidget(flags)
        vert.addWidget(Note("Affects %s. Changes will NOT be retroactive to "
                            "old MP3s. If needed, you may want to regenerate "
                            "MP3s and/or clear the cache (Advanced tab)." %
                            ', '.join(rtr.by_trait(rtr.Trait.TRANSCODING))))

        group = QtGui.QGroupBox("LAME Transcoder")
        group.setLayout(vert)
        return group

    def _ui_tabs_mp3gen_throttle(self):
        """Returns the "Download Throttling" input group."""

        threshold = QtGui.QSpinBox()
        threshold.setObjectName('throttle_threshold')
        threshold.setRange(5, 1000)
        threshold.setSingleStep(5)
        threshold.setSuffix(" operations")

        sleep = QtGui.QSpinBox()
        sleep.setObjectName('throttle_sleep')
        sleep.setRange(15, 10800)
        sleep.setSingleStep(15)
        sleep.setSuffix(" seconds")

        hor = QtGui.QHBoxLayout()
        hor.addWidget(Label("After "))
        hor.addWidget(threshold)
        hor.addWidget(Label(" sleep for "))
        hor.addWidget(sleep)
        hor.addStretch()

        rtr = self._addon.router
        vert = QtGui.QVBoxLayout()
        vert.addWidget(Note("Tweak how often AwesomeTTS takes a break when "
                            "mass downloading files from online services."))
        vert.addLayout(hor)
        vert.addWidget(Note("Affects %s." %
                            ', '.join(rtr.by_trait(rtr.Trait.INTERNET))))

        group = QtGui.QGroupBox("Download Throttling during Batch Processing")
        group.setLayout(vert)
        return group

    def _ui_tabs_windows(self):
        """Returns the "Window" tab."""

        grid = QtGui.QGridLayout()
        for i, (desc, sub) in enumerate([
                ("open configuration in main window", 'configurator'),
                ("insert <tts> tag in template editor", 'templater'),
                ("mass generate MP3s in card browser", 'browser_generator'),
                ("mass remove audio in card browser", 'browser_stripper'),
                ("generate single MP3 in note editor*", 'editor_generator'),
        ]):
            grid.addWidget(Label("To " + desc + ", strike"), i, 0)
            grid.addWidget(self._factory_shortcut('launch_' + sub), i, 1)
        grid.setColumnStretch(1, 1)

        group = QtGui.QGroupBox("Window Shortcuts")
        group.setLayout(grid)

        vert = QtGui.QVBoxLayout()
        vert.addWidget(group)
        vert.addWidget(Note(
            "* By default, AwesomeTTS binds %(native)s for most actions. If "
            "you use math equations and LaTeX with Anki using the %(native)s "
            "E/M/T keystrokes, you may want to reassign or unbind the "
            "shortcut for generating in the note editor." %
            dict(native=key_combo_desc(QtCore.Qt.ControlModifier |
                                       QtCore.Qt.Key_T))
        ))
        vert.addWidget(Note("Editor and browser shortcuts will take effect "
                            "the next time you open those windows."))
        vert.addWidget(Note("Some keys cannot be used as shortcuts and some "
                            "keystrokes might not work in some windows, "
                            "depending on your operating system and other "
                            "add-ons you are running. You may have to "
                            "experiment to find what works best."))
        vert.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(vert)
        return tab

    def _ui_tabs_advanced(self):
        """Returns the "Advanced" tab."""

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._ui_tabs_advanced_presets())
        layout.addWidget(self._ui_tabs_advanced_update())
        layout.addWidget(self._ui_tabs_advanced_debug())
        layout.addWidget(self._ui_tabs_advanced_cache())
        layout.addStretch()

        tab = QtGui.QWidget()
        tab.setLayout(layout)
        return tab

    def _ui_tabs_advanced_presets(self):
        """Returns the "Presets" input group."""

        button = QtGui.QPushButton("Manage...")
        button.clicked.connect(self._on_presets)

        hor = QtGui.QHBoxLayout()
        hor.addWidget(Label("Save services for quick access or side-click "
                            "playback."))
        hor.addSpacing(self._SPACING)
        hor.addWidget(button)
        hor.addStretch()

        group = QtGui.QGroupBox("Service Presets")
        group.setLayout(hor)
        return group

    def _ui_tabs_advanced_update(self):
        """Returns the "Updates" input group."""

        button = QtGui.QPushButton(QtGui.QIcon(':/icons/find.png'),
                                   "Check Now")
        button.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        button.setObjectName('updates_button')
        button.clicked.connect(self._on_update_request)

        state = Note()
        state.setObjectName('updates_state')

        hor = QtGui.QHBoxLayout()
        hor.addWidget(button)
        hor.addWidget(state)

        vert = QtGui.QVBoxLayout()
        vert.addWidget(Checkbox("automatically check for AwesomeTTS updates "
                                "at start-up", 'updates_enabled'))
        vert.addLayout(hor)

        group = QtGui.QGroupBox("Updates")
        group.setLayout(vert)
        return group

    def _ui_tabs_advanced_debug(self):
        """Returns the "Write Debugging Output" input group."""

        vert = QtGui.QVBoxLayout()

        if self._addon.paths.in_ascii:
            vert.addWidget(Checkbox("standard output (stdout)",
                                    'debug_stdout'))
            vert.addWidget(Checkbox("log file in add-on directory",
                                    'debug_file'))
        else:
            vert.addWidget(Note("Unfortunately, logging is not available "
                                "when running AwesomeTTS from a directory "
                                "with non-ASCII characters."))

        group = QtGui.QGroupBox("Write Debugging Output")
        group.setLayout(vert)
        return group

    def _ui_tabs_advanced_cache(self):
        """Returns the "Media Cache" input group."""

        button = QtGui.QPushButton("Clear Cache")
        button.setObjectName('on_cache')
        button.clicked.connect(lambda: self._on_cache_clear(button))

        layout = QtGui.QVBoxLayout()
        layout.addWidget(button)
        layout.addWidget(Note("Audio is cached for successive playback and "
                              "recording. This improves performance, notably "
                              "when using on-the-fly playback, but you may "
                              "want to clear it from time to time."))

        group = QtGui.QGroupBox("Media Cache")
        group.setLayout(layout)
        return group

    # Factories ##############################################################

    def _factory_shortcut(self, object_name):
        """Returns a push button capable of being assigned a shortcut."""

        shortcut = QtGui.QPushButton()
        shortcut.atts_pending = False
        shortcut.setObjectName(object_name)
        shortcut.setCheckable(True)
        shortcut.toggled.connect(
            lambda is_down: (
                shortcut.setText("press keystroke"),
                shortcut.setFocus(),  # needed for OS X if text inputs present
            ) if is_down
            else shortcut.setText(key_combo_desc(shortcut.atts_value))
        )
        return shortcut

    # Events #################################################################

    def show(self, *args, **kwargs):
        """Restores state on inputs; rough opposite of the accept()."""

        for widget, value in [
                (widget, self._addon.config[widget.objectName()])
                for widget in self.findChildren(self._PROPERTY_WIDGETS)
                if widget.objectName() in self._PROPERTY_KEYS
        ]:
            if isinstance(widget, Checkbox):
                widget.setChecked(value)
                widget.stateChanged.emit(value)
            elif isinstance(widget, QtGui.QLineEdit):
                widget.setText(value)
            elif isinstance(widget, QtGui.QPushButton):
                widget.atts_value = value
                widget.setText(key_combo_desc(widget.atts_value))
            elif isinstance(widget, QtGui.QComboBox):
                widget.setCurrentIndex(max(widget.findData(value), 0))
            elif isinstance(widget, QtGui.QSpinBox):
                widget.setValue(value)
            elif isinstance(widget, QtGui.QListView):
                widget.setModel(value)

        widget = self.findChild(QtGui.QPushButton, 'on_cache')
        if widget:
            widget.atts_list = (
                [filename for filename in os.listdir(self._addon.paths.cache)]
                if os.path.isdir(self._addon.paths.cache) else []
            )

            if len(widget.atts_list):
                widget.setEnabled(True)
                widget.setText("Clear Cache (%s item%s)" % (
                    locale("%d", len(widget.atts_list), grouping=True),
                    "" if len(widget.atts_list) == 1 else "s",
                ))
            else:
                widget.setEnabled(False)
                widget.setText("Clear Cache (no items)")

        super(Configurator, self).show(*args, **kwargs)

    def accept(self):
        """Saves state on inputs; rough opposite of show()."""

        for list_view in self.findChildren(QtGui.QListView):
            for editor in list_view.findChildren(QtGui.QWidget, 'editor'):
                list_view.commitData(editor)  # if an editor is open, save it

        self._addon.config.update({
            widget.objectName(): (
                widget.isChecked() if isinstance(widget, Checkbox)
                else widget.atts_value if isinstance(widget, QtGui.QPushButton)
                else widget.value() if isinstance(widget, QtGui.QSpinBox)
                else widget.itemData(widget.currentIndex()) if isinstance(
                    widget, QtGui.QComboBox)
                else [
                    i for i in widget.model().raw_data
                    if i['compiled'] and 'bad_replace' not in i
                ] if isinstance(widget, QtGui.QListView)
                else widget.text()
            )
            for widget in self.findChildren(self._PROPERTY_WIDGETS)
            if widget.objectName() in self._PROPERTY_KEYS
        })

        super(Configurator, self).accept()

    def help_request(self):
        """Launch browser to the URL for the user's current tab."""

        tabs = self.findChild(QtGui.QTabWidget)
        self._launch_link('config/' +
                          tabs.tabText(tabs.currentIndex()).lower())

    def keyPressEvent(self, key_event):  # from PyQt4, pylint:disable=C0103
        """Assign new combo for shortcut buttons undergoing changes."""

        buttons = self._get_pressed_shortcut_buttons()
        if not buttons:
            return super(Configurator, self).keyPressEvent(key_event)

        key = key_event.key()

        if key == QtCore.Qt.Key_Escape:
            for button in buttons:
                button.atts_pending = False
                button.setText(key_combo_desc(button.atts_value))
            return

        if key in [QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete]:
            combo = None
        else:
            combo = key_event_combo(key_event)
            if not combo:
                return

        for button in buttons:
            button.atts_pending = combo
            button.setText(key_combo_desc(combo))

    def keyReleaseEvent(self, key_event):  # from PyQt4, pylint:disable=C0103
        """Disengage all shortcut buttons undergoing changes."""

        buttons = self._get_pressed_shortcut_buttons()
        if not buttons:
            return super(Configurator, self).keyReleaseEvent(key_event)

        elif key_event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            # need to ignore and eat key release on enter/return so that user
            # can activate the button without immediately deactivating it
            return

        for button in buttons:
            if button.atts_pending is not False:
                button.atts_value = button.atts_pending
            button.setChecked(False)

    def _get_pressed_shortcut_buttons(self):
        """Returns all shortcut buttons that are pressed."""

        return [button
                for button in self.findChildren(QtGui.QPushButton)
                if (button.isChecked() and
                    (button.objectName().startswith('launch_') or
                     button.objectName().startswith('tts_key_')))]

    def _on_presets(self):
        """Opens the presets editor."""

        if not self._preset_editor:
            self._preset_editor = _PresetEditor(addon=self._addon,
                                                alerts=self._alerts,
                                                ask=self._ask,
                                                parent=self)
        self._preset_editor.show()

    def _on_update_request(self):
        """Attempts update request w/ add-on updates interface."""

        button = self.findChild(QtGui.QPushButton, 'updates_button')
        button.setEnabled(False)
        state = self.findChild(Note, 'updates_state')
        state.setText("Querying update server...")

        from .updater import Updater
        self._addon.updates.check(
            callbacks=dict(
                done=lambda: button.setEnabled(True),
                fail=lambda exception: state.setText("Check failed: %s" % (
                    exception.message or format(exception) or
                    "Nothing further known"
                )),
                good=lambda: state.setText("No update needed at this time."),
                need=lambda version, info: (
                    state.setText("Update to %s is available" % version),
                    [updater.show()
                     for updater in [Updater(
                         version=version,
                         info=info,
                         is_manual=True,
                         addon=self._addon,
                         parent=(self if self.isVisible()
                                 else self.parentWidget()),
                     )]],
                ),
            ),
        )

    def _on_cache_clear(self, button):
        """Attempts clear known files from cache."""

        button.setEnabled(False)
        count_error = count_success = 0

        for filename in button.atts_list:
            try:
                os.unlink(os.path.join(self._addon.paths.cache, filename))
                count_success += 1
            except:  # capture all exceptions, pylint:disable=W0702
                count_error += 1

        if count_error:
            if count_success:
                button.setText("partially emptied cache (%s item%s left)" % (
                    locale("%d", count_error, grouping=True),
                    "" if count_error == 1 else "s",
                ))
            else:
                button.setText("unable to empty cache")
        else:
            button.setText("successfully emptied cache")


class _PresetEditor(ServiceDialog):
    """Provides a dialog for editing presets."""

    __slots__ = []

    def __init__(self, *args, **kwargs):
        super(_PresetEditor, self).__init__(title="Manage Service Presets",
                                            *args, **kwargs)

    # UI Construction ########################################################

    def _ui_control(self):
        """Add explanation of the preset functionality."""

        header = Label("About Service Presets")
        header.setFont(self._FONT_HEADER)

        layout = super(_PresetEditor, self)._ui_control()
        layout.addWidget(header)
        layout.addWidget(Note(
            'Once saved, your service option presets can be easily recalled '
            'in most AwesomeTTS dialog windows and/or used for on-the-fly '
            'playback with <tts preset="..."> ... </tts> template tags.'
        ))
        layout.addWidget(Note(
            "Selecting text and then side-clicking in some Anki panels (e.g. "
            "review mode, card layout editor, note editor fields) will also "
            "allow playback of the selected text using any of your presets."
        ))
        layout.addSpacing(self._SPACING)
        layout.addStretch()
        layout.addWidget(self._ui_buttons())

        return layout

    def _ui_buttons(self):
        """Removes the "Cancel" button."""

        buttons = super(_PresetEditor, self)._ui_buttons()
        for btn in buttons.buttons():
            if buttons.buttonRole(btn) == QtGui.QDialogButtonBox.RejectRole:
                buttons.removeButton(btn)
        return buttons

    # Events #################################################################

    def accept(self):
        """Remember the user's options if they hit "Okay"."""

        self._addon.config.update(self._get_all())
        super(_PresetEditor, self).accept()

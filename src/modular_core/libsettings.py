import modular_core.libfundamental as lfu

import types,os,pdb

settings = {}

if __name__ == 'modular_core.libsettings':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__': print 'this is a library!'

class settings_manager(lfu.mobject):

    true_strings = ['true','True','On','on']
    false_strings = ['false','False','Off','off']

    def __init__(self,*args,**kwargs):
        self._default('settings',{},**kwargs)
        self._default('settings_types',{},**kwargs)
        self._default('filename',None,**kwargs)
        lfu.mobject.__init__(self,*args,**kwargs)
        if lgm:self.mason = lgm.standard_mason()
        self.cfg_path = lfu.get_resource_path()

    def write_settings(self, filename = 'settings.txt'):
        if self.filename: filename = self.filename
        settings_path = os.path.join(self.cfg_path, filename)
        lines = ['']
        for key in self.settings.keys():
            lines.append('')
            lines.append('<' + key + '>')
            for sub_key in self.settings[key].keys():
                lines.append(' = '.join([sub_key, str(
                        self.settings[key][sub_key])]))

        with open(settings_path, 'w') as handle:
            handle.writelines([line + '\n' for line in lines])

    def read_settings(self, filename = 'settings.txt'):
        if self.filename: filename = self.filename
        settings_path = os.path.join(self.cfg_path, filename)
        if not os.path.exists(settings_path):
            settings_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(settings_path):
            print 'cannot find settings file!', filename
            return None
        with open(settings_path, 'r') as handle:
            lines = [l.strip() for l in handle.readlines()]
        parser = ''
        key_lines = [line.strip() for line in lines if 
                    line.strip().startswith('<') and 
                        line.strip().endswith('>')]
        for line in lines:
            if line.startswith('#') == True or line.strip() == '':
                continue

            elif line.strip() in key_lines:
                parser = line.strip()[1:-1]
                if not parser in self.settings.keys():
                    self.settings[parser] = {}
                    self.settings_types[parser] = {}

                continue

            else:
                eq_dex = line.find('=')
                value = line[eq_dex + 1:].strip()
                key = line[:eq_dex].strip()
                #if the value is some variant of 'true'
                if value in self.true_strings:
                    self.settings[parser][key] = True
                    self.settings_types[parser][key] = bool

                #elif the value is some variant of 'false'
                elif value in self.false_strings:
                    self.settings[parser][key] = False
                    self.settings_types[parser][key] = bool

                else:
                    try:
                        #if int cast is equivalent to float cast, int
                        if int(value) == float(value):
                            self.settings[parser][key] = int(value)
                            self.settings_types[parser][key] = int

                        #else float cast is assumed equivalent
                        else:
                            self.settings[parser][key] = float(value)
                            self.settings_types[parser][key] = float

                    #if not boolean, int, or float, assumed string
                    except ValueError:
                        self.settings[parser][key] = value
                        self.settings_types[parser][key] = str

        global settings
        settings = self.settings
        return self.settings

    def revert_settings(self):
        self.read_settings()
        self.display()

    def display(self):
        self._widget()
        self.panel = lgb.create_scroll_area(
            lgb.create_panel(self.widg_templates, self.mason))
        self.panel.setGeometry(150, 120, 384, 512)
        self.panel.show()

    def generate_bool_widget_template(self, key, sub_key):
        template = lgm.interface_template_gui(
                    widgets = ['check_set'], 
                    verbosities = [0], 
                    instances = [[self.settings[key]]], 
                    append_instead = [False], 
                    keys = [[sub_key]], 
                    labels = [[sub_key]])
        return template

    def generate_int_widget_template(self, key, sub_key):
        template = lgm.interface_template_gui(
                    widgets = ['spin'], 
                    verbosities = [0], 
                    instances = [[self.settings[key]]], 
                    keys = [[sub_key]], 
                    initials = [[self.settings[key][sub_key]]], 
                    box_labels = [sub_key])
        return template

    def generate_string_widget_template(self, key, sub_key):
        template = lgm.interface_template_gui(
                    widgets = ['text'], 
                    verbosities = [0], 
                    inst_is_dict = [(True, self)], 
                    instances = [[self.settings[key]]], 
                    keys = [[sub_key]], 
                    initials = [[self.settings[key][sub_key]]], 
                    box_labels = [sub_key])
        return template

    def _widget(self, *args, **kwargs):
        self._sanitize(*args, **kwargs)
        sub_panel_templates = []
        for key in self.settings.keys():
            sub_panel_templates.append((key, []))
            for sub_key in self.settings[key].keys():
                setting_type = self.settings_types[key][sub_key]
                if setting_type is types.BooleanType:
                    sub_panel_templates[-1][1].append(
                        self.generate_bool_widget_template(
                                            key, sub_key))

                elif setting_type is types.IntType:
                    sub_panel_templates[-1][1].append(
                        self.generate_int_widget_template(
                                            key, sub_key))

                elif setting_type is types.StringType:
                    sub_panel_templates[-1][1].append(
                        self.generate_string_widget_template(
                                                key, sub_key))

        [self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['panel'], 
                verbosities = [0], 
                templates = [sub_panel_templates[panel_dex][1]], 
                box_labels = [sub_panel_templates[panel_dex][0]], 
                panel_position = (panel_dex + 1, 0))) for 
                    panel_dex in range(len(self.settings.keys()))]
        self.widg_templates.append(
            lgm.interface_template_gui(
                widgets = ['button_set'], 
                verbosities = [0], 
                layouts = ['horizontal'], 
                bindings = [[self.write_settings, self.revert_settings]], 
                labels = [['Save Settings', 'Revert Settings']]))
        lfu.mobject._widget(self,*args,from_sub = True)

def get_setting(setting, fail_silent = False, 
        default_from_file = True, file_ = ''):
    for key in settings.keys():
        if setting in settings[key].keys():
            return settings[key][setting]

    if default_from_file and file_:
        man = settings_manager(filename = file_)
        man.read_settings()
        sett = get_setting(setting, fail_silent = False)
        print 'found setting', setting, ': ', sett, 'in default file', file_
        return sett

    if not fail_silent: print 'could not find setting', setting

def set_setting(setting, to_set_to, save_ = False, file_ = None):
    for key in settings.keys():
        if setting in settings[key].keys():
            settings[key][setting] = to_set_to

    if save_ and not file_ is None:
        # there is likely a bug here since the program could be using a settings_manager
        #  that is no longer up to date.... flag for reread?
        man = settings_manager()
        man.settings = settings
        man.write_settings(filename = file_)











from datetime import datetime
import os
from urllib.parse import parse_qs, urlparse
from tool import ToolUtil
from flask import Response
from .setup import *

try:
    if os.path.exists(os.path.join(os.path.dirname(__file__), "source_afrtv_handler.py")):
        from .source_afrtv_handler import AFRTV_Handler

    else:
        from support import SupportSC

        AFRTV_Handler = SupportSC.load_module_f(__file__, "source_afrtv_handler").AFRTV_Handler
except:
    pass


class ModuleMain(PluginModuleBase):
    def __init__(self, P):
        super(ModuleMain, self).__init__(P, name="main", first_menu="setting", scheduler_desc="아프리카TV")
        self.db_default = {
            f"{self.name}_db_version": "1",
            f"{self.name}_auto_start": "False",
            f"{self.name}_interval": "5",
            "plex_server_url": "http://localhost:32400",
            "plex_token": "",
            "plex_meta_item": "",
            "yaml_path": "",
            "use_quality": "1920x1080",
            "streaming_type": "redirect",
            "use_top": "True",
            "use_user": "False",
            "use_hot": "False",
        }

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg["api_m3u"] = ToolUtil.make_apikey_url(f"/{P.package_name}/api/m3u")
        arg["api_yaml"] = ToolUtil.make_apikey_url(f"/{P.package_name}/api/yaml")
        arg["hls_playback"] = "https://chrome.google.com/webstore/detail/native-hls-playback/emnphkkblegpebimobpbekeedfgemhof"
        if sub == "setting":
            arg["is_include"] = F.scheduler.is_include(self.get_scheduler_name())
            arg["is_running"] = F.scheduler.is_running(self.get_scheduler_name())
        return render_template(f"{P.package_name}_{self.name}_{sub}.html", arg=arg)

    def process_command(self, command, arg1, arg2, arg3, req):
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        streaming_type = P.ModelSetting.get("streaming_type")

        if command == "broad_list":
            return jsonify({"list": AFRTV_Handler.ch_list(), "updated_at": updated_at, "streaming_type": streaming_type})
        elif command == "play_url":
            url = arg1
            ret = {"ret": "success", "data": url}
        return jsonify(ret)

    def process_api(self, sub, req):
        try:
            if sub == "m3u":
                return AFRTV_Handler.make_m3u()
            elif sub == "yaml":
                return AFRTV_Handler.make_yaml()
            elif sub == "url.m3u8":
                return AFRTV_Handler.url_m3u8(req)
            elif sub == "play":
                return AFRTV_Handler.play(req)
            elif sub == "segment":
                return AFRTV_Handler.segment(req)

        except Exception as e:
            P.logger.error(f"Exception:{str(e)}")
            P.logger.error(traceback.format_exc())

    def scheduler_function(self):
        try:
            AFRTV_Handler.sync_yaml_data()
        except Exception as e:
            P.logger.error(f"Exception:{str(e)}")
            P.logger.error(traceback.format_exc())

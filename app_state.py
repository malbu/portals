class AppState:
    def __init__(self, my_id, peer_info, keymap):
        self.my_id = my_id
        self.peer_info = peer_info
        self.keymap = keymap
        self.view_mode = 'SINGLE'
        self.other_ids = [pid for pid in peer_info if pid != my_id]
        self.single_target = self.other_ids[0] if self.other_ids else None


    def handle_key(self, k):
        act = self.keymap.get(k)
        if act == 'quit':
            return 'QUIT'
        if act == 'toggle_dual_view':
            if len(self.other_ids) < 2:
                return None
            self.view_mode = 'DUAL' if self.view_mode == 'SINGLE' else 'SINGLE'
            return 'MODE'
        if act in self.other_ids and self.view_mode == 'SINGLE':
            self.single_target = act
            return 'VIEW'
        return None


    def current_single_ip(self):
        return self.peer_info[self.single_target]['ip'] if self.single_target else None


    def current_single_name(self):
        return self.peer_info[self.single_target]['name'] if self.single_target else 'N/A'


    def dual_targets(self):
        return [self.peer_info[pid] for pid in self.other_ids[:2]] if len(self.other_ids) >= 1 else []

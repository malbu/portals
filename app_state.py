class AppState:
    def __init__(self, my_id, peer_info, keymap):
        self.my_id = my_id
        self.peer_info = peer_info
        self.keymap = keymap
        self.view_mode = 'SINGLE'
        self.other_ids = [pid for pid in peer_info if pid != my_id]
        self.single_target = self.other_ids[0] if self.other_ids else None  # default target


    def handle_key(self, k):
        act = self.keymap.get(k)
        if act == 'quit':
            return 'QUIT'

        # rotate through single-view peer 1 -> single-view peer 2 -> dual view 
        if act == 'rotate_view':
            return self._rotate_view()

        return None

    def _rotate_view(self):
        """Advance the view mode in the sequence:

        single(other_ids[0]) -> single(other_ids[1]) -> dual ->single(other_ids[0]) -> …
        Edge case for testing:  Fewer than two peers are available; dual view is skipped
        Returns:
        status string consumed by the caller to decide whether a UI
        update is needed: 
        1) 'VIEW' when only the single-target changed
         2) 'MODE' when view_mode changed
        3) else None
        """

        num_peers = len(self.other_ids)
        if num_peers == 0:
            return None

        # currently in SINGLE view
        if self.view_mode == 'SINGLE':
            try:
                idx = self.other_ids.index(self.single_target)
            except ValueError:
                idx = 0

            if num_peers >= 2 and idx == 0:  # switch to peer #2 single view
                self.single_target = self.other_ids[1]
                return 'VIEW'

            # either there is only one peer, or already showing peer #2
            if num_peers >= 2:
                self.view_mode = 'DUAL'
                return 'MODE'
            else:
                # only one peer, nothing to rotate
                return None

        # currently in DUAL view -> go back to first peer single view
        else:
            self.view_mode = 'SINGLE'
            self.single_target = self.other_ids[0]
            return 'MODE'


    def current_single_ip(self):
        return self.peer_info[self.single_target]['ip'] if self.single_target else None


    def current_single_name(self):
        return self.peer_info[self.single_target]['name'] if self.single_target else 'N/A'


    def dual_targets(self):
        return [self.peer_info[pid] for pid in self.other_ids[:2]] if len(self.other_ids) >= 1 else []

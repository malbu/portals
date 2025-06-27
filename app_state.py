class AppState:
    """
    view_mode values:
        SINGLE  ``single_target``
        DUAL    first two peers in ``other_ids``
        TRANSITION clip playing, new view pending activation
    """

    #  represents the local camera feed in the case where there is only one remote peer
    LOCAL = '__LOCAL__'

    def __init__(self, my_id, peer_info, keymap):
        self.my_id = my_id
        self.peer_info = peer_info
        self.keymap = keymap

        # remote only list
        self.other_ids = [pid for pid in peer_info if pid != my_id]
        # if there is only one peer, allow remote to local toggle
        self._toggle_with_local = (len(self.other_ids) == 1)

        self.view_mode: str = 'SINGLE'
        if self.other_ids:
            self.single_target = self.other_ids[0]
        elif self._toggle_with_local:
            self.single_target = self.LOCAL
        else:
            self.single_target = None

        # pending view requested while a transition clip is playing
        self._pending_mode = None  # type: str | None
        self._pending_target = None  # type: str | None


    def handle_key(self, k):
        """Return action dict understood by main loop

        Possible return values:
            {'action': 'QUIT'}
            {'action': 'SWITCH', 'next_mode': <mode>, 'next_target': <target or None>}
            
        """

        act = self.keymap.get(k)
        if act == 'quit':
            return {'action': 'QUIT'}

        if act == 'rotate_view':
            next_mode, next_target = self._compute_next_view()
            if next_mode:
                return {
                    'action': 'SWITCH',
                    'next_mode': next_mode,
                    'next_target': next_target,
                }
        return None


    def _compute_next_view(self):
        """determine what the next view would be without mutating state"""

        num_peers = len(self.other_ids)
        if num_peers == 0 and not self._toggle_with_local:
            return None, None

        if self.view_mode == 'SINGLE':
            try:
                idx = self.other_ids.index(self.single_target)
            except ValueError:
                idx = 0

            if num_peers >= 2 and idx == 0:
                # switch to peer #2 single view
                return 'SINGLE', self.other_ids[1]

            if num_peers >= 2:
                # move to dual view
                return 'DUAL', None

            if num_peers == 1 and self._toggle_with_local:
                # toggle between remote peer and LOCAL
                return ('SINGLE',
                        self.LOCAL if self.single_target == self.other_ids[0]
                                    else self.other_ids[0])
            return None, None

        elif self.view_mode == 'DUAL':
            # go back to first peer single view
            return 'SINGLE', self.other_ids[0]

        elif self.view_mode == 'TRANSITION':
            # currently showing clip; ignore rotations until finished
            return None, None

        return None, None


    def queue_pending_view(self, mode, single_target=None):
        """enter TRANSITION mode and remember the target view

        called by main loop when a clip will be shown
        """
        self._pending_mode = mode
        self._pending_target = single_target
        self.view_mode = 'TRANSITION'

    def activate_view(self, mode, single_target=None):
        self.view_mode = mode
        if mode == 'SINGLE':
            self.single_target = single_target

    def activate_pending_view(self):
        if self._pending_mode is None:
            return
        self.activate_view(self._pending_mode, self._pending_target)
        self._pending_mode = None
        self._pending_target = None


    def current_single_ip(self):
        if self.single_target in (None, self.LOCAL):
            return None
        return self.peer_info[self.single_target]['ip']

    def current_single_name(self):
        if self.single_target == self.LOCAL:
            return self.peer_info[self.my_id]['name']
        if self.single_target:
            return self.peer_info[self.single_target]['name']
        return 'N/A'

    def dual_targets(self):
        return [self.peer_info[pid] for pid in self.other_ids[:2]] if len(self.other_ids) >= 1 else []

    def current_view_peer_ips(self):
        """return list of IDs currently onscreen (remote IPs or LOCAL tag)"""
        if self.view_mode == 'SINGLE':
            if self.single_target == self.LOCAL:
                return [self.LOCAL]
            ip = self.current_single_ip()
            return [ip] if ip else []
        elif self.view_mode == 'DUAL':
            return [t['ip'] for t in self.dual_targets()]
        else:
            return []

    def single_is_local(self):
        return self.single_target == self.LOCAL

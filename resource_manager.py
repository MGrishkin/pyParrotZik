import sys
from BeautifulSoup import BeautifulSoup
import ParrotProtocol


class ResourceManagerBase(object):
    resources = [
    ]

    def __init__(self, socket, resource_values=None):
        self.sock = socket
        self.resource_values = resource_values or {}

    def get(self, resource):
        try:
            return self.resource_values[resource]
        except KeyError:
            return self.fetch(resource)

    def fetch(self, resource):
        assert resource in self.resources, 'Unknown resource {}'.format(resource)
        assert 'get' in self.resources[resource], 'Unhandled method'
        message = ParrotProtocol.getRequest(resource + '/get')
        result = self.send_message(message)
        self.resource_values[resource] = result
        return result

    def toggle_on(self, resource):
        assert resource in self.resources, 'Unknown resource {}'.format(resource)
        assert 'enable' in self.resources[resource], 'Unhandled method'
        message = ParrotProtocol.getRequest(resource + '/enable')
        self.send_message(message)
        self.fetch(resource)

    def toggle_off(self, resource):
        assert resource in self.resources, 'Unknown resource {}'.format(resource)
        assert 'disable' in self.resources[resource], 'Unhandled method'
        message = ParrotProtocol.getRequest(resource + '/disable')
        self.send_message(message)
        self.fetch(resource)

    def set(self, resource, arg):
        assert resource in self.resources, 'Unknown resource {}'.format(resource)
        assert 'set' in self.resources[resource], 'Unhandled method'
        message = ParrotProtocol.setRequest(resource + '/set', str(arg).lower())
        self.send_message(message)
        self.fetch(resource)

    def send_message(self, message):
        try:
            self.sock.send(str(message))
        except Exception:
            self.sock = ""
            return
        else:
            return self.get_answer()

    def get_answer(self):
        data = self.receive_message()
        while not data.answer:
            if data.notify:
                self.handle_notification(data.notify)
            else:
                raise AssertionError('Unknown response')
            data = self.receive_message()
        return data.answer

    def handle_notification(self, notification):

        self.fetch(notification['path'].rsplit('/', 1)[0].encode('utf-8'))

    def receive_message(self):
        if sys.platform == "darwin":
            self.sock.recv(30)
        else:
            self.sock.recv(7)
        return BeautifulSoup(self.sock.recv(1024))

    def close(self):
        self.sock.close()


class GenericResourceManager(ResourceManagerBase):
    resources = {
        '/api/software/version': ['get'],
    }

    def __init__(self, sock):
        super(GenericResourceManager, self).__init__(sock)
        self.notifications = []

    def handle_notification(self, notification):
        self.notifications.append(notification)

    def get_resource_manager(self, resource_manager_class):
        resource_manager = resource_manager_class(self.sock, self.resource_values)
        for notitifaction in self.notifications:
            resource_manager.handle_notification(notitifaction)
        return resource_manager

    @property
    def api_version(self):
        answer = self.get("/api/software/version")
        try:
            return answer.software["version"]
        except KeyError:
            return answer.software['sip6']


class Version1ResourceManager(ResourceManagerBase):
    resources = {
        '/api/software/version': ['get'],
        '/api/system/battery': ['get'],
        '/api/bluetooth/friendlyname': ['get'],
        '/api/system/auto_connection/enabled': ['get', 'set'],
        '/api/system/anc_phone_mode/enabled': ['get', 'set'],
        '/api/audio/specific_mode/enabled': ['get', 'set'],
        '/api/audio/sound_effect/enabled': ['get', 'set'],
        '/api/audio/noise_cancellation/enabled': ['get', 'set'],
    }

class Version2ResourceManager(ResourceManagerBase):
    resources = {
        '/api/software/version': ['get'],
        '/api/system/battery': ['get'],
        '/api/system/pi': ['get'],
        '/api/bluetooth/friendlyname': ['get'],
        '/api/system/auto_connection/enabled': ['get', 'set'],
        '/api/system/anc_phone_mode/enabled': ['get', 'set'],
        '/api/flight_mode': ['get', 'enable', 'disable'],
        '/api/audio/sound_effect/enabled': ['get', 'set'],
        '/api/audio/sound_effect/room_size': ['get', 'set'],
        '/api/audio/sound_effect/angle': ['get', 'set'],
        '/api/audio/noise': ['get'],
        '/api/audio/noise_control': ['get'],
        '/api/audio/noise_control/enabled': ['get', 'set'],
        '/api/audio/track/metadata': ['get'],
    }

class Publisher(object):
    def __init__(self):
        self.subscribers = []

    def subscribe(self, who):
        if who not in self.subscribers:
            self.subscribers.append(who)

    def unsubscribe(self, who):
        if who in self.subscribers:
            self.subscribers.remove(who)

    def request_all(self, message, *args):
        method = "request_" + message
        ret = []
        for subscriber in self.subscribers:
            if hasattr(subscriber, method):
                ret.append(getattr(subscriber, method)(*args))
        return ret

    def request_one(self, message, *args):
        method = "request_" + message
        for subscriber in self.subscribers:
            if hasattr(subscriber, method):
                return getattr(subscriber, method)(*args)

    def notify(self, message, *args):
        method = "msg_" + message
        for subscriber in self.subscribers:
            if hasattr(subscriber, method):
                getattr(subscriber, method)(*args)

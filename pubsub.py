class Publisher(object):
    def __init__(self):
        self.subscribers = []

    def subscribe(self, who):
        if who not in self.subscribers:
            self.subscribers.append(who)

    def unsubscribe(self, who):
        if who in self.subscribers:
            self.subscribers.remove(who)

    def publish(self, message, *args):
        for subscriber in self.subscribers:
            method = "msg_" + message
            if hasattr(subscriber, method):
                getattr(subscriber, method)(*args)

from django.db import models


class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField('event date')
    url = models.URLField('event url', default='')
    resale_active = models.BooleanField(default=False)

    def __str__(self):
        return f"<Event(title={self.title}, url={self.url})>"


class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    price = models.CharField(max_length=100)
    available = models.BooleanField(default=False)
    ignore = models.BooleanField(default=False)

    def __str__(self):
        return (f"<Ticket(title={self.title}, event={self.event.title}, "
                f"available={self.available})>")


class Tracker(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    email = models.EmailField()
    datetime = models.DateTimeField(auto_now_add=True)
    sent = models.BooleanField(default=False)

    def __str__(self):
        return (f"<Tracker(event={self.event.title}, email={self.email}, "
                f"sent={self.sent})>")

import functools

from django.dispatch import receiver


def receiver_ignores_dumpdata(signal, **decorator_kwargs):
    def our_wrapper(func):
        @receiver(signal, **decorator_kwargs)
        @functools.wraps(func)
        def fake_receiver(sender, **kwargs):
            if kwargs.get("raw"):
                return
            return func(sender, **kwargs)

        return fake_receiver

    return our_wrapper

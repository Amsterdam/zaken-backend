from api.tasks import GenericUserTask


class CreateSignal(GenericUserTask):
    task_name = "task_create_signal"
    description = "Nieuwe melding verwerken"
    # asynchronous = True  # TODO should be async right?

    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class SIAFeedbackReporters(GenericUserTask):
    task_name = "Activity_19a40xb"
    description = "SIA terugkoppeling melder(s)"

    @staticmethod
    def get_steps():
        return [
            *CreateSignal.get_steps(),
            __class__(),
        ]


class Correspondence(GenericUserTask):
    task_name = "task_correspondence"
    description = "Oppakken correspondentie"
    # asynchronous = True  # TODO should be async right?

    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class CallbackRequest(GenericUserTask):
    task_name = "task_callback_request"
    description = "Oppakken terugbelverzoek"
    # asynchronous = True  # TODO should be async right?

    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class SubmitObjectionFile(GenericUserTask):
    task_name = "task_submit_objectionfile"
    description = "Aanleveren bezwaardossier"
    # asynchronous = True  # TODO should be async right?

    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]


class AddExtraInformation(GenericUserTask):
    task_name = "task_add_extra_information"
    description = "Verwerken extra informatie"
    # asynchronous = True  # TODO should be async right?

    @staticmethod
    def get_steps():
        return [
            # *X.get_steps(),  # TODO what is the preceiding step?
            __class__(),
        ]

from abc import ABC, abstractmethod
from typing import Optional


class AbstractBackend(ABC):

    @abstractmethod
    def write_flow(self, text: str, project_name: str, *args, **kwargs):
        pass

    @abstractmethod
    async def async_write_flow(self, text: str, project_name: str, *args, **kwargs):
        pass


class AbstractAlarmBackend(ABC):
    alarmer_name: Optional[str] = None
    alarm_required_fields: Optional[str] = ['example']
    _custom_backend_name: Optional[str] = 'CustomBackend'

    @abstractmethod
    async def async_write_flow(self, text: str, project_name: str, *args, **kwargs):
        pass


    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)

        if not hasattr(cls.__init__, '__code__') or cls.alarm_required_fields == ['example']:
            for field in cls.alarm_required_fields:
                setattr(instance, field, None)
        else:
            init_params = cls.__init__.__code__.co_varnames[1:cls.__init__.__code__.co_argcount]

            missing_params = [field for field in cls.alarm_required_fields if field not in init_params]
            if missing_params:
                raise TypeError(
                    f"Class '{cls.__name__}' is missing constructor parameters: {', '.join(missing_params)}"
                )

            extra_params = [param for param in init_params if param not in cls.alarm_required_fields]
            if extra_params:
                raise TypeError(
                    f"Class '{cls.__name__}' has extra constructor parameters not defined in 'alarm_required_fields': "
                    f"{', '.join(extra_params)}"
                )

        return instance

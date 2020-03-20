import attr
import os
from typing import Union, Any

from provisioner import inputs
from .salt import provisioner_cmd
from .commands import commands
from .errors import ProvisionerError


# TODO TESTS
@attr.s(auto_attribs=True)
class SimpleRunner:
    nowait: bool = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "run the command as a salt job in async mode"
            }
        }, default=False
    )

    @classmethod
    def fill_parser(cls, parser):
        inputs.ParserFiller.fill_parser(cls, parser)

    # TODO TYPING
    def run(self, command: Union[str, Any], *args, **kwargs):

        # TODO DOCS environment variable
        # TODO use config instead of (or in addition to) env variable

        # TODO IMPROVE
        salt_job = (
            (command != 'get_result') and
            (self.nowait or (os.getenv('PRVSNR_SALT_JOB', 'no') == 'yes'))
        )

        if salt_job:
            try:
                return provisioner_cmd(
                    command,
                    fun_args=args,
                    fun_kwargs=kwargs,
                    nowait=self.nowait
                )
            except ProvisionerError:
                raise
            except Exception as exc:
                raise ProvisionerError(repr(exc)) from exc
        else:
            cmd = commands[command]
            return cmd.run(*args, **kwargs)

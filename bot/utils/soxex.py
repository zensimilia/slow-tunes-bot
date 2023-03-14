from sox import Transformer, file_info
from sox.core import sox, SoxError

from .logger import get_logger

logger = get_logger()


class ExtTransformer(Transformer):
    """Extend sox.Transformer class for bitrate support."""

    def build(
        self,
        input_filepath=None,
        output_filepath=None,
        input_array=None,
        sample_rate_in=None,
        extra_args=None,
        return_output=False,
        bitrate=None,
    ):
        '''
        Given an input file, creates an output_file on disk by
        executing the current set of commands. This function returns True on
        success. If return_output is True, this function returns a triple of
        (status, out, err), giving the success state, along with stdout and
        stderr returned by sox.

        Parameters
        ----------
        input_filepath : str or None
            Either path to input audio file or None for array input.
        output_filepath : str
            Path to desired output file. If a file already exists at
            the given path, the file will be overwritten.
            If '-n', no file is created.
        input_array : np.ndarray or None
            An np.ndarray of an waveform with shape (n_samples, n_channels).
            sample_rate_in must also be provided.
            If None, input_filepath must be specified.
        sample_rate_in : int
            Sample rate of input_array.
            This argument is ignored if input_array is None.
        extra_args : list or None, default=None
            If a list is given, these additional arguments are passed to SoX
            at the end of the list of effects.
            Don't use this argument unless you know exactly what you're doing!
        return_output : bool, default=False
            If True, returns the status and information sent to stderr and
            stdout as a tuple (status, stdout, stderr).
            If output_filepath is None, return_output=True by default.
            If False, returns True on success.
        bitrate : float
            Bitrate of output file or None.

        Returns
        -------
        status : bool
            True on success.
        out : str (optional)
            This is not returned unless return_output is True.
            When returned, captures the stdout produced by sox.
        err : str (optional)
            This is not returned unless return_output is True.
            When returned, captures the stderr produced by sox.
        '''

        input_format, input_filepath = self._parse_inputs(
            input_filepath, input_array, sample_rate_in
        )

        if output_filepath is None:
            raise ValueError("output_filepath is not specified!")

        # set output parameters
        if input_filepath == output_filepath:
            raise ValueError(
                "input_filepath must be different from output_filepath."
            )
        file_info.validate_output_file(output_filepath)

        args = []
        args.extend(self.globals)
        args.extend(self._input_format_args(input_format))
        args.append(input_filepath)
        args.extend(self._output_format_args(self.output_format))

        if bitrate is not None:
            if not isinstance(bitrate, float):
                raise ValueError("bitrate must be a float.")
            args.extend(['-C', '{:f}'.format(bitrate)])

        args.append(output_filepath)
        args.extend(self.effects)

        if extra_args is not None:
            if not isinstance(extra_args, list):
                raise ValueError("extra_args must be a list.")
            args.extend(extra_args)

        status, out, err = sox(args, input_array, True)
        if status != 0:
            raise SoxError("Stdout: {}\nStderr: {}".format(out, err))

        logger.info(
            "Created %s with effects: %s",
            output_filepath,
            " ".join(self.effects_log),
        )

        if return_output:
            return status, out, err

        return True

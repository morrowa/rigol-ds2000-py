# Python Utils for Rigol DS2000 Series

This code depends on [PyVISA](https://github.com/pyvisa/pyvisa) and [NumPy](https://github.com/numpy/numpy). Both can be installed using pip. You will also need a backend for PyVISA; see its documentation for how to install one.

The first argument to each public function must be a PyVISA resource instance. For example:

    ```python
    import pyvisa
    rm = pyvisa.ResourceManager()
    # Grabs the first instrument of any kind. If your scope is connected via USB, this probably works
    rigol = rm.open_resource(rm.list_resources()[0])

    import ds2102a
    # reads the current waveform on the screen for channel 1 without stopping the scope
    # returns a numpy.ndarray of floating point voltages
    # (note the raw output of the scope is unsigned 8b values that we normalize to voltages)
    y_vals = ds2102a.read_normal(rigol)
    ```

If you want to use time values (i.e. seconds) instead of point indices for your X-values, the `last_x_values` function outputs the offset of each sample from the trigger in integer picoseconds.


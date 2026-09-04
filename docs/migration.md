# Note for future maintainers: `ucc/package/bin/assets.py`

`bin/assets.py` is created by hand, not `ucc-gen`-generated (see its docstring). It uses the
legacy AOB-style `splunktaucclib.modinput_wrapper.BaseModInput` + `input_module_assets.py`
`collect_events(helper, ew)`/`validate_input(helper, definition)` pattern, because `ucc-gen`'s
native templates don't support that function signature.

The more "native" long-term alternative is `ucc-gen`'s `inputHelperModule` globalConfig key,
which auto-generates the wrapper for you, but requires rewriting `input_module_assets.py` to
the different `stream_events(inputs, ew)`/`validate_input(definition)` signature (no `helper`
object -- checkpointing/proxy/logging must be reimplemented against `solnlib`/`smi` directly).

To adapt to this:
- Read `input.template` and the `_add_modular_input`/`inputHelperModule` handling in
  `commands/build.py`, both inside the installed `splunk_add_on_ucc_framework` package
  (`ucc/.venv/lib/python*/site-packages/splunk_add_on_ucc_framework/`).
- Reference implementation: any current `ucc-gen` example add-on using `inputHelperModule`
  in [addonfactory-ucc-generator](https://github.com/splunk/addonfactory-ucc-generator)'s test
  fixtures.
- Once migrated, delete `ucc/package/bin/assets.py` and add `"inputHelperModule":
  "input_module_assets"` to the `assets` service in `ucc/globalConfig.json`.

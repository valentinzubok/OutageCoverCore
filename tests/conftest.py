"""Pytest bootstrap: a fake GenVM the tests steer.

Knobs:
  gl.clock              the transaction datetime, in unix seconds (see advance())
  gl.page               text the source page returns (str, or an Exception to raise)
  gl.llm_reply          raw model output (str/dict, or an Exception to raise)
  gl.comparative_fails  when True, eq_principle.prompt_comparative raises
  gl.prompts            every prompt sent, for assertions about quoting
  gl.balance            GEN (wei) the contract holds; pay() adds to it, payouts subtract
  gl.transfers          every external wallet transfer the contract emitted: (address, wei)
"""

from __future__ import annotations

import sys
import types
from pathlib import Path


PAGE_1 = "Month 1 report. DONE: the indexer was shipped and released as v0.1.0 on 5 January."
PAGE_2 = "Month 2 report. DONE: the public API was shipped and released as v0.2.0 on 3 February."
PAGE_3 = "Month 3 report. DONE: the docs site was published and v1.0.0 was released on 2 March."


def _install_fake_genlayer() -> None:
    existing = sys.modules.get("genlayer")
    if existing is not None and getattr(existing, "_fake_genvm", False):
        return

    gl = types.ModuleType("genlayer")
    gl._fake_genvm = True

    class _Write:
        """`@gl.public.write` and `@gl.public.write.payable`."""

        def __call__(self, fn):
            fn._payable = False
            return fn

        @staticmethod
        def payable(fn):
            fn._payable = True
            return fn

    class _Public:
        write = _Write()

        @staticmethod
        def view(fn):
            return fn

    class TreeMap(dict):
        """`genlayer.storage.TreeMap`: a persistent map. `TreeMap[str, str]` is the class."""

        def __class_getitem__(cls, item):
            return cls

    class DynArray(list):
        """`genlayer.storage.DynArray`: a persistent list."""

        def __class_getitem__(cls, item):
            return cls

    class _Contract:
        """Base class: a contract can read its own balance. Typed storage fields start empty,
        as they do in GenVM."""

        def __new__(cls, *args, **kwargs):
            obj = super().__new__(cls)
            for name, kind in getattr(cls, "__annotations__", {}).items():
                label = kind if isinstance(kind, str) else getattr(kind, "__name__", "")
                if label.startswith("TreeMap"):
                    setattr(obj, name, TreeMap())
                elif label.startswith("DynArray"):
                    setattr(obj, name, DynArray())
            return obj

        @property
        def balance(self):
            return gl.balance

    class _WalletProxy:
        def __init__(self, address):
            self.address = str(address)

        def emit_transfer(self, value=0, **kwargs):
            """An external native transfer. It cannot send what the contract does not hold."""
            if kwargs:
                raise TypeError("external transfers take no `on` argument")
            amount = int(value)
            if amount <= 0 or amount > gl.balance:
                raise Exception("transfer exceeds the contract balance")
            gl.balance -= amount
            gl.transfers.append((self.address, amount))

    def _evm_interface(cls):
        return _WalletProxy

    class _EqPrinciple:
        @staticmethod
        def prompt_comparative(leader_fn, principle="", /):
            """`principle` is positional-only in GenVM v0.3; the fake enforces that so a
            keyword call fails in tests exactly as it does on chain."""
            if getattr(gl, "comparative_fails", False):
                raise Exception("comparative consensus unavailable")
            return leader_fn()

        @staticmethod
        def strict_eq(leader_fn):
            return leader_fn()

    def _render(url, mode="text"):
        # gl.pages maps a URL to its text (or an Exception); anything else returns gl.page.
        page = gl.pages.get(url, gl.page)
        if isinstance(page, Exception):
            raise page
        return page

    def _exec_prompt(prompt, response_format=None):
        gl.prompts.append(prompt)
        reply = gl.llm_reply
        if isinstance(reply, Exception):
            raise reply
        return reply

    class UserError(Exception):
        """`gl.vm.UserError`: the error a contract raises on purpose."""

        def __init__(self, message=""):
            super().__init__(message)
            self.message = message

    gl.contract = types.SimpleNamespace(Contract=_Contract)
    gl.Contract = _Contract
    gl.vm = types.SimpleNamespace(UserError=UserError)
    gl.gl = gl  # `from genlayer import *` brings `gl` into the contract module
    gl.Address = str
    gl.public = _Public()
    gl.evm = types.SimpleNamespace(contract_interface=_evm_interface)
    gl.message = types.SimpleNamespace(
        sender_address="0x1111111111111111111111111111111111111111", value=0
    )
    gl_types = types.ModuleType("genlayer.types")
    gl_types.Address = str
    gl.types = gl_types
    sys.modules["genlayer.types"] = gl_types
    gl_storage = types.ModuleType("genlayer.storage")
    gl_storage.TreeMap = TreeMap
    gl_storage.DynArray = DynArray
    gl.storage = gl_storage
    sys.modules["genlayer.storage"] = gl_storage
    gl.eq_principle = _EqPrinciple()
    gl.nondet = types.SimpleNamespace(
        web=types.SimpleNamespace(render=_render),
        exec_prompt=_exec_prompt,
    )

    gl.clock = 1_767_225_600  # 2026-01-01T00:00:00Z — tests move it with advance()
    gl.page = PAGE_1
    gl.llm_reply = '{"incident": true}'
    gl.comparative_fails = False
    gl.prompts = []
    gl.balance = 0
    gl.pages = {}
    gl.transfers = []
    sys.modules["genlayer"] = gl


def load_contract(repo_root: Path, filename: str = "OutageCover.py"):
    """Load the contract, with the clock wired to gl.clock.

    On chain, `datetime.now()` returns the transaction datetime: deterministic, identical
    for every validator. The stub below reproduces that so every time rule can be
    tested without sleeping, and so a test cannot accidentally depend on wall-clock time.
    """
    _install_fake_genlayer()
    gl = sys.modules["genlayer"]
    path = repo_root / "contracts" / filename
    mod_name = f"contract_{filename.replace('.', '_')}"
    module = types.ModuleType(mod_name)
    module.__dict__["gl"] = gl
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)

    real_datetime = module.__dict__["datetime"]

    class _TxDatetime(real_datetime):  # type: ignore[misc, valid-type]
        @classmethod
        def now(cls, tz=None):
            return real_datetime.fromtimestamp(gl.clock, tz)

    module.__dict__["datetime"] = _TxDatetime
    sys.modules[mod_name] = module
    return module


def advance(gl, seconds: int) -> None:
    """Move the transaction clock forward, e.g. past an interval or a deadline."""
    gl.clock += int(seconds)


def reset(gl) -> None:
    gl.clock = 1_767_225_600  # 2026-01-01T00:00:00Z — tests move it with advance()
    gl.page = PAGE_1
    gl.llm_reply = '{"incident": true}'
    gl.comparative_fails = False
    gl.prompts = []
    gl.balance = 0
    gl.pages = {}
    gl.transfers = []
    gl.message.value = 0
    gl.message.sender_address = "0x1111111111111111111111111111111111111111"


def pay(gl, method, value: int, *args):
    """Call a contract method with `value` wei attached, the way the network does it.

    The value reaches the contract balance whether or not the call succeeds: on the real
    network a reverted call does not return what was attached. A non-payable method
    refuses value outright.
    """
    if value and not getattr(method, "_payable", False):
        raise Exception("method is not payable")
    gl.message.value = int(value)
    gl.balance += int(value)
    try:
        return method(*args)
    finally:
        gl.message.value = 0

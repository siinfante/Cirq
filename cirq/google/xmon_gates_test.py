# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
import numpy as np
from google.protobuf import message, text_format

import cirq
from cirq.api.google.v1 import operations_pb2
from cirq.devices import GridQubit
from cirq.google import (
    XmonGate, XmonMeasurementGate, ExpZGate, Exp11Gate, ExpWGate,
)
from cirq.study import ParamResolver
from cirq.value import Symbol


def proto_matches_text(proto: message, expected_as_text: str):
    expected = text_format.Merge(expected_as_text, type(proto)())
    return str(proto) == str(expected)


def test_parameterized_value_from_proto():
    from_proto = XmonGate.parameterized_value_from_proto

    m1 = operations_pb2.ParameterizedFloat(raw=5)
    assert from_proto(m1) == 5

    with pytest.raises(ValueError):
        from_proto(operations_pb2.ParameterizedFloat())

    m3 = operations_pb2.ParameterizedFloat(parameter_key='rr')
    assert from_proto(m3) == Symbol('rr')


def test_measurement_eq():
    eq = cirq.testing.EqualsTester()
    eq.make_equality_group(lambda: XmonMeasurementGate(key=''))
    eq.make_equality_group(lambda: XmonMeasurementGate('a'))
    eq.make_equality_group(lambda: XmonMeasurementGate('b'))
    eq.make_equality_group(lambda: XmonMeasurementGate(key='',
                                                      invert_mask=(True,)))
    eq.make_equality_group(lambda: XmonMeasurementGate(key='',
                                                      invert_mask=(False,)))


def test_single_qubit_measurement_to_proto():
    assert proto_matches_text(
        XmonMeasurementGate('test').to_proto(GridQubit(2, 3)),
        """
        measurement {
            targets {
                row: 2
                col: 3
            }
            key: "test"
        }
        """)


def test_multi_qubit_measurement_to_proto():
    assert proto_matches_text(
        XmonMeasurementGate('test').to_proto(GridQubit(2, 3), GridQubit(3, 4)),
        """
        measurement {
            targets {
                row: 2
                col: 3
            }
            targets {
                row: 3
                col: 4
            }
            key: "test"
        }
        """)


def test_z_eq():
    eq = cirq.testing.EqualsTester()
    eq.make_equality_group(lambda: ExpZGate(half_turns=0))
    eq.add_equality_group(ExpZGate(),
                          ExpZGate(half_turns=1),
                          ExpZGate(degs=180),
                          ExpZGate(rads=np.pi))
    eq.make_equality_group(
        lambda: ExpZGate(half_turns=Symbol('a')))
    eq.make_equality_group(
        lambda: ExpZGate(half_turns=Symbol('b')))
    eq.add_equality_group(
        ExpZGate(half_turns=-1.5),
        ExpZGate(half_turns=10.5))


def test_z_to_proto():
    assert proto_matches_text(
        ExpZGate(half_turns=Symbol('k')).to_proto(
            GridQubit(2, 3)),
        """
        exp_z {
            target {
                row: 2
                col: 3
            }
            half_turns {
                parameter_key: "k"
            }
        }
        """)

    assert proto_matches_text(
        ExpZGate(half_turns=0.5).to_proto(
            GridQubit(2, 3)),
        """
        exp_z {
            target {
                row: 2
                col: 3
            }
            half_turns {
                raw: 0.5
            }
        }
        """)


def test_z_matrix():
    assert np.allclose(ExpZGate(half_turns=1).matrix(),
                       np.array([[-1j, 0], [0, 1j]]))
    assert np.allclose(ExpZGate(half_turns=0.5).matrix(),
                       np.array([[1 - 1j, 0], [0, 1 + 1j]]) / np.sqrt(2))
    assert np.allclose(ExpZGate(half_turns=0).matrix(),
                       np.array([[1, 0], [0, 1]]))
    assert np.allclose(ExpZGate(half_turns=-0.5).matrix(),
                       np.array([[1 + 1j, 0], [0, 1 - 1j]]) / np.sqrt(2))


def test_z_parameterize():
    parameterized_gate = ExpZGate(half_turns=Symbol('a'))
    assert parameterized_gate.is_parameterized()
    with pytest.raises(ValueError):
        _ = parameterized_gate.matrix()
    resolver = ParamResolver({'a': 0.1})
    resolved_gate = parameterized_gate.with_parameters_resolved_by(resolver)
    assert resolved_gate == ExpZGate(half_turns=0.1)


def test_cz_eq():
    eq = cirq.testing.EqualsTester()
    eq.make_equality_group(lambda: Exp11Gate(half_turns=0))
    eq.add_equality_group(Exp11Gate(),
                          Exp11Gate(half_turns=1),
                          Exp11Gate(degs=180),
                          Exp11Gate(rads=np.pi))
    eq.make_equality_group(lambda: Exp11Gate(half_turns=Symbol('a')))
    eq.make_equality_group(lambda: Exp11Gate(half_turns=Symbol('b')))
    eq.add_equality_group(
        Exp11Gate(half_turns=-1.5),
        Exp11Gate(half_turns=6.5))


def test_cz_to_proto():
    assert proto_matches_text(
        Exp11Gate(half_turns=Symbol('k')).to_proto(
            GridQubit(2, 3), GridQubit(4, 5)),
        """
        exp_11 {
            target1 {
                row: 2
                col: 3
            }
            target2 {
                row: 4
                col: 5
            }
            half_turns {
                parameter_key: "k"
            }
        }
        """)

    assert proto_matches_text(
        Exp11Gate(half_turns=0.5).to_proto(
            GridQubit(2, 3), GridQubit(4, 5)),
        """
        exp_11 {
            target1 {
                row: 2
                col: 3
            }
            target2 {
                row: 4
                col: 5
            }
            half_turns {
                raw: 0.5
            }
        }
        """)


def test_cz_potential_implementation():
    assert not cirq.can_cast(cirq.KnownMatrix,
                             Exp11Gate(half_turns=Symbol('a')))
    assert cirq.can_cast(cirq.KnownMatrix, Exp11Gate())


def test_cz_parameterize():
    parameterized_gate = Exp11Gate(half_turns=Symbol('a'))
    assert parameterized_gate.is_parameterized()
    with pytest.raises(ValueError):
        _ = parameterized_gate.matrix()
    resolver = ParamResolver({'a': 0.1})
    resolved_gate = parameterized_gate.with_parameters_resolved_by(resolver)
    assert resolved_gate == Exp11Gate(half_turns=0.1)


def test_w_eq():
    eq = cirq.testing.EqualsTester()
    eq.add_equality_group(ExpWGate(),
                          ExpWGate(half_turns=1, axis_half_turns=0),
                          ExpWGate(degs=180, axis_degs=0),
                          ExpWGate(rads=np.pi, axis_rads=0))
    eq.make_equality_group(
        lambda: ExpWGate(half_turns=Symbol('a')))
    eq.make_equality_group(lambda: ExpWGate(half_turns=0))
    eq.make_equality_group(
        lambda: ExpWGate(half_turns=0,
                         axis_half_turns=Symbol('a')))
    eq.add_equality_group(
        ExpWGate(half_turns=0, axis_half_turns=0.5),
        ExpWGate(half_turns=0, axis_rads=np.pi / 2))
    eq.make_equality_group(
        lambda: ExpWGate(
            half_turns=Symbol('ab'),
            axis_half_turns=Symbol('xy')))

    # Flipping the axis and negating the angle gives the same rotation.
    eq.add_equality_group(
        ExpWGate(half_turns=0.25, axis_half_turns=1.5),
        ExpWGate(half_turns=1.75, axis_half_turns=0.5))
    # ...but not when there are parameters.
    eq.add_equality_group(ExpWGate(
        half_turns=Symbol('a'),
        axis_half_turns=1.5))
    eq.add_equality_group(ExpWGate(
        half_turns=Symbol('a'),
        axis_half_turns=0.5))
    eq.add_equality_group(ExpWGate(
        half_turns=0.25,
        axis_half_turns=Symbol('a')))
    eq.add_equality_group(ExpWGate(
        half_turns=1.75,
        axis_half_turns=Symbol('a')))

    # Adding or subtracting whole turns/phases gives the same rotation.
    eq.add_equality_group(
        ExpWGate(
            half_turns=-2.25, axis_half_turns=1.25),
        ExpWGate(
            half_turns=7.75, axis_half_turns=11.25))


def test_w_to_proto():
    assert proto_matches_text(
        ExpWGate(half_turns=Symbol('k'),
                 axis_half_turns=1).to_proto(
            GridQubit(2, 3)),
        """
        exp_w {
            target {
                row: 2
                col: 3
            }
            axis_half_turns {
                raw: 1
            }
            half_turns {
                parameter_key: "k"
            }
        }
        """)

    assert proto_matches_text(
        ExpWGate(half_turns=0.5,
                 axis_half_turns=Symbol('j')).to_proto(
            GridQubit(2, 3)),
        """
        exp_w {
            target {
                row: 2
                col: 3
            }
            axis_half_turns {
                parameter_key: "j"
            }
            half_turns {
                raw: 0.5
            }
        }
        """)


def test_w_potential_implementation():
    assert not cirq.can_cast(cirq.KnownMatrix, ExpWGate(half_turns=Symbol('a')))
    assert not cirq.can_cast(cirq.ReversibleEffect,
                             ExpWGate(half_turns=Symbol('a')))
    assert cirq.can_cast(cirq.KnownMatrix, ExpWGate())
    assert cirq.can_cast(cirq.ReversibleEffect, ExpWGate())


def test_w_parameterize():
    parameterized_gate = ExpWGate(half_turns=Symbol('a'),
                                  axis_half_turns=Symbol('b'))
    assert parameterized_gate.is_parameterized()
    with pytest.raises(ValueError):
        _ = parameterized_gate.matrix()
    resolver = ParamResolver({'a': 0.1, 'b': 0.2})
    resolved_gate = parameterized_gate.with_parameters_resolved_by(resolver)
    assert resolved_gate == ExpWGate(half_turns=0.1, axis_half_turns=0.2)


def test_trace_bound():
    assert ExpZGate(half_turns=.001).trace_distance_bound() < 0.01
    assert ExpWGate(half_turns=.001).trace_distance_bound() < 0.01
    assert ExpZGate(half_turns=cirq.Symbol('a')).trace_distance_bound() >= 1
    assert ExpWGate(half_turns=cirq.Symbol('a')).trace_distance_bound() >= 1


def test_has_inverse():
    assert ExpZGate(half_turns=.1).has_inverse()
    assert ExpWGate(half_turns=.1).has_inverse()
    assert not ExpZGate(half_turns=cirq.Symbol('a')).has_inverse()
    assert not ExpWGate(half_turns=cirq.Symbol('a')).has_inverse()


def test_measure_key_on():
    q = GridQubit(0, 0)

    assert XmonMeasurementGate(key='').on(q) == cirq.GateOperation(
        gate=XmonMeasurementGate(key=''),
        qubits=(q,))
    assert XmonMeasurementGate(key='a').on(q) == cirq.GateOperation(
        gate=XmonMeasurementGate(key='a'),
        qubits=(q,))


def test_symbol_diagrams():
    q00 = cirq.GridQubit(0, 0)
    q01 = cirq.GridQubit(0, 1)
    c = cirq.Circuit.from_ops(
        cirq.google.ExpWGate(axis_half_turns=cirq.Symbol('a'),
                             half_turns=cirq.Symbol('b')).on(q00),
        cirq.google.ExpZGate(half_turns=cirq.Symbol('c')).on(q01),
        cirq.google.Exp11Gate(half_turns=cirq.Symbol('d')).on(q00, q01),
    )
    assert c.to_text_diagram() == """
(0, 0): ?????????W(a)^b?????????@???????????????
                    ???
(0, 1): ?????????Z^c??????????????????@^d?????????
    """.strip()


def test_z_diagram_chars():
    q = cirq.GridQubit(0, 1)
    c = cirq.Circuit.from_ops(
        cirq.google.ExpZGate().on(q),
        cirq.google.ExpZGate(half_turns=0.5).on(q),
        cirq.google.ExpZGate(half_turns=0.25).on(q),
        cirq.google.ExpZGate(half_turns=0.125).on(q),
        cirq.google.ExpZGate(half_turns=-0.5).on(q),
        cirq.google.ExpZGate(half_turns=-0.25).on(q),
    )
    assert c.to_text_diagram() == """
(0, 1): ?????????Z?????????S?????????T?????????Z^0.125?????????S^-1?????????T^-1?????????
    """.strip()


def test_w_diagram_chars():
    q = cirq.GridQubit(0, 1)
    c = cirq.Circuit.from_ops(
        cirq.google.ExpWGate(axis_half_turns=0).on(q),
        cirq.google.ExpWGate(axis_half_turns=0.25).on(q),
        cirq.google.ExpWGate(axis_half_turns=0.5).on(q),
        cirq.google.ExpWGate(axis_half_turns=cirq.Symbol('a')).on(q),
    )
    assert c.to_text_diagram() == """
(0, 1): ?????????X?????????W(0.25)?????????Y?????????W(a)?????????
    """.strip()

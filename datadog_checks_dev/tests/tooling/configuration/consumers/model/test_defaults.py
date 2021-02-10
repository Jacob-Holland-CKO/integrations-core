# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import pytest

from ...utils import get_model_consumer, normalize_yaml

pytestmark = [pytest.mark.conf, pytest.mark.conf_consumer, pytest.mark.conf_consumer_model]


def test():
    consumer = get_model_consumer(
        """
        name: test
        version: 0.0.0
        files:
        - name: test.yaml
          options:
          - template: instances
            options:
            - name: foo
              required: true
              description: words
              value:
                type: string
            - name: example
              description: words
              value:
                example: bar
                type: string
            - name: default_precedence
              description: words
              value:
                example: bar
                default: baz
                type: string
            - name: example_ignored_array
              description: words
              value:
                example:
                - test
                type: array
                items:
                  type: string
            - name: example_ignored_object
              description: words
              value:
                example:
                  key: value
                type: object
                additionalProperties: true
            - name: long_default_formatted
              description: words
              value:
                default:
                - ["01", "02", "03", "04", "05"]
                - ["06", "07", "08", "09", "10"]
                - ["11", "12", "13", "14", "15"]
                - ["16", "17", "18", "19", "20"]
                - ["21", "22", "23", "24", "25"]
                type: array
                items:
                  type: array
                  items:
                    type: string
        """
    )

    model_definitions = consumer.render()
    assert len(model_definitions) == 1

    files = model_definitions['test.yaml']
    assert len(files) == 4

    validators_contents, validators_errors = files['validators.py']
    assert not validators_errors
    assert validators_contents == ''

    package_root_contents, package_root_errors = files['__init__.py']
    assert not package_root_errors
    assert package_root_contents == normalize_yaml(
        """
        from .instance import InstanceConfig
        """
    )

    defaults_contents, defaults_errors = files['defaults.py']
    assert not defaults_errors
    assert defaults_contents == normalize_yaml(
        """
        from datadog_checks.base.utils.models.fields import get_default_field_value
        from datadog_checks.base.utils.models.utils import make_immutable_check_config


        def instance_default_precedence(field, value):
            return make_immutable_check_config('baz')


        def instance_example(field, value):
            return make_immutable_check_config('bar')


        def instance_example_ignored_array(field, value):
            return get_default_field_value(field, value)


        def instance_example_ignored_object(field, value):
            return get_default_field_value(field, value)


        def instance_long_default_formatted(field, value):
            return make_immutable_check_config(
                [
                    ['01', '02', '03', '04', '05'],
                    ['06', '07', '08', '09', '10'],
                    ['11', '12', '13', '14', '15'],
                    ['16', '17', '18', '19', '20'],
                    ['21', '22', '23', '24', '25'],
                ]
            )
        """
    )

    instance_model_contents, instance_model_errors = files['instance.py']
    assert not instance_model_errors
    assert instance_model_contents == normalize_yaml(
        """
        from __future__ import annotations

        from typing import Any, Mapping, Optional, Sequence

        from pydantic import BaseModel, root_validator, validator

        from datadog_checks.base.utils.functions import identity

        from . import defaults, validators


        class InstanceConfig(BaseModel):
            class Config:
                allow_mutation = False

            default_precedence: Optional[str]
            example: Optional[str]
            example_ignored_array: Optional[Sequence[str]]
            example_ignored_object: Optional[Mapping[str, Any]]
            foo: str
            long_default_formatted: Optional[Sequence[Sequence[str]]]

            @validator('default_precedence', pre=True, always=True)
            def _ensure_default_default_precedence(cls, v, field):
                return defaults.instance_default_precedence(field, v) if v is None else v

            @validator('example', pre=True, always=True)
            def _ensure_default_example(cls, v, field):
                return defaults.instance_example(field, v) if v is None else v

            @validator('example_ignored_array', pre=True, always=True)
            def _ensure_default_example_ignored_array(cls, v, field):
                return defaults.instance_example_ignored_array(field, v) if v is None else v

            @validator('example_ignored_object', pre=True, always=True)
            def _ensure_default_example_ignored_object(cls, v, field):
                return defaults.instance_example_ignored_object(field, v) if v is None else v

            @validator('long_default_formatted', pre=True, always=True)
            def _ensure_default_long_default_formatted(cls, v, field):
                return defaults.instance_long_default_formatted(field, v) if v is None else v

            @validator('default_precedence', always=True)
            def _validate_default_precedence(cls, v, field):
                return getattr(validators, 'instance_default_precedence', identity)(v, field=field)

            @validator('example', always=True)
            def _validate_example(cls, v, field):
                return getattr(validators, 'instance_example', identity)(v, field=field)

            @validator('example_ignored_array', always=True)
            def _validate_example_ignored_array(cls, v, field):
                return getattr(validators, 'instance_example_ignored_array', identity)(v, field=field)

            @validator('example_ignored_object', always=True)
            def _validate_example_ignored_object(cls, v, field):
                return getattr(validators, 'instance_example_ignored_object', identity)(v, field=field)

            @validator('foo', always=True)
            def _validate_foo(cls, v, field):
                return getattr(validators, 'instance_foo', identity)(v, field=field)

            @validator('long_default_formatted', always=True)
            def _validate_long_default_formatted(cls, v, field):
                return getattr(validators, 'instance_long_default_formatted', identity)(v, field=field)

            @root_validator
            def _final_validation(cls, values):
                return getattr(validators, 'final', identity)(values)
        """
    )

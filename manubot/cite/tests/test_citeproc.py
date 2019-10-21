import json
import pathlib

import pytest

from manubot.cite.citeproc import (
    csl_item_passthrough,
    append_to_csl_item_note,
    parse_csl_item_note,
    remove_jsonschema_errors,
)

directory = pathlib.Path(__file__).parent
csl_instances = [
    x.name for x in directory.glob('csl-json/*-csl')
]


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

    
def test_json_is_readable_on_windows_in_different_oem_encoding():
    name = 'crossref-deep-review-csl'
    path = directory / 'csl-json' / name / 'raw.json'
    content = path.read_text(encoding='utf-8-sig')
    assert content
    json1 = load_json(path)
    assert json1


def test_csl_item_passthrough():
    ci1 = csl_item_passthrough(dict(type='chapter', id='abc'), prune=True)
    ci2 = csl_item_passthrough(dict(type='chapter'), set_id='abc', prune=True)
    assert ci1 == {'type': 'chapter', 'id': 'abc'}
    assert ci2 == {'type': 'chapter', 'id': 'abc'}


@pytest.mark.parametrize('name', csl_instances)
def test_remove_jsonschema_errors(name):
    """
    Tests whether CSL pruning of raw.json produces the expected pruned.json.
    The fidelity of the remove_jsonschema_errors implementation is
    difficult to assess theoretically, therefore its performance should be
    evaluated empirically with thorough test coverage. It is recommended that
    all conceivable conformations of invalid CSL that citeproc methods may
    generate be tested.

    To create a new test case, derive pruned.json from raw.json, by manually
    deleting any invalid fields. Do not use `manubot cite` to directly generate
    pruned.json as that also relies on remove_jsonschema_errors for pruning.
    """
    data_dir = directory / 'csl-json' / name
    raw = load_json(data_dir / 'raw.json')
    expected = load_json(data_dir / 'pruned.json')
    pruned = remove_jsonschema_errors(raw)
    assert pruned == expected


@pytest.mark.parametrize(['input_note', 'text', 'dictionary', 'expected_note'], [
    ('preexisting note', '', {}, 'preexisting note'),
    ('preexisting note', '', {'key': 'the value'}, 'preexisting note\nkey: the value'),
    ('', '', {'KEYOKAY': 'the value'}, 'KEYOKAY: the value'),
    ('preexisting note', '', {'KEY-NOT-OKAY': 'the value'}, 'preexisting note'),
    ('', '', {'standard_citation': 'doi:10.7554/elife.32822'}, 'standard_citation: doi:10.7554/elife.32822'),
    ('This CSL Item was produced using Manubot.', '', {'standard_citation': 'doi:10.7554/elife.32822'}, 'This CSL Item was produced using Manubot.\nstandard_citation: doi:10.7554/elife.32822'),
])
def test_append_to_csl_item_note(input_note, text, dictionary, expected_note):
    csl_item = {
        'id': 'test_csl_item',
        'type': 'entry',
        'note': input_note,
    }
    append_to_csl_item_note(csl_item, text, dictionary)
    output_note = csl_item['note']
    assert output_note == expected_note


@pytest.mark.parametrize(['note', 'dictionary'], [
    ('This is a note\nkey_one: value\nKEYTWO: value 2 ', {'key_one': 'value', 'KEYTWO': 'value 2'}),
    ('BAD_KEY: good value\ngood-key: good value', {'good-key': 'good value'}),
    ('This is a note {:key_one: value} {:KEYTWO: value 2 } ', {'key_one': 'value', 'KEYTWO': 'value 2'}),
    ('{:BAD_KEY: good value}\n{:good-key: good value}', {'good-key': 'good value'}),
    ('Mixed line-entry and braced-entry syntax\nGOODKEY: good value\n{:good-key: good value}', {'GOODKEY': 'good value', 'good-key': 'good value'}),
    ('Note without any key-value pairs', {}),
    ('Other text\nstandard_citation: doi:10/ckcj\nMore other text', {'standard_citation': 'doi:10/ckcj'}),
])
def test_parse_csl_item_note(note, dictionary):
    assert parse_csl_item_note(note) == dictionary

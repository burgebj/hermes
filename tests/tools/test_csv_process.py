"""Tests for CSV processing tool."""

import json
import os
import pytest
import tempfile

from tools.csv_process import csv_process, _select_columns, _filter_rows, _aggregate


class TestCsvProcess:
    @pytest.fixture
    def temp_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('name,age,city\n')
            f.write('Alice,25,NYC\n')
            f.write('Bob,30,LA\n')
            f.write('Charlie,35,NYC\n')
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.fixture
    def empty_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('name,age\n')
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_read_success(self, temp_csv):
        result = json.loads(csv_process('read', temp_csv))
        assert result['success'] is True
        assert result['row_count'] == 3
        assert result['columns'] == ['name', 'age', 'city']
        assert len(result['data']) == 3

    def test_read_empty_file(self, empty_csv):
        result = json.loads(csv_process('read', empty_csv))
        assert result['success'] is True
        assert result['row_count'] == 0

    def test_read_file_not_found(self):
        result = json.loads(csv_process('read', '/nonexistent/file.csv'))
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_filter_greater_than(self, temp_csv):
        result = json.loads(csv_process('filter', temp_csv, filter_condition='age > 28'))
        assert result['success'] is True
        assert result['original_count'] == 3
        assert result['filtered_count'] == 2

    def test_filter_equality(self, temp_csv):
        result = json.loads(csv_process('filter', temp_csv, filter_condition="city == 'NYC'"))
        assert result['success'] is True
        assert result['filtered_count'] == 2

    def test_filter_with_columns(self, temp_csv):
        result = json.loads(csv_process('filter', temp_csv, filter_condition='age > 28', columns=['name']))
        assert result['success'] is True
        assert 'name' in result['data'][0]

    def test_transform_select_columns(self, temp_csv):
        result = json.loads(csv_process('transform', temp_csv, columns=['name', 'age']))
        assert result['success'] is True
        assert result['columns'] == ['name', 'age']
        assert result['row_count'] == 3

    def test_aggregate_numeric(self, temp_csv):
        result = json.loads(csv_process('aggregate', temp_csv, columns=['age']))
        assert result['success'] is True
        assert 'age' in result['results']
        assert result['results']['age']['count'] == 3
        assert result['results']['age']['sum'] == 90
        assert result['results']['age']['avg'] == 30

    def test_aggregate_empty_file(self, empty_csv):
        result = json.loads(csv_process('aggregate', empty_csv, columns=['age']))
        assert result['success'] is True
        assert result['results'] == {}

    def test_export_success(self, temp_csv):
        output_path = temp_csv.replace('.csv', '_output.csv')
        result = json.loads(csv_process('export', temp_csv, output_path=output_path))
        assert result['success'] is True
        assert result['row_count'] == 3
        assert os.path.exists(output_path)
        os.remove(output_path)

    def test_export_requires_output_path(self, temp_csv):
        result = json.loads(csv_process('export', temp_csv, output_path=None))
        assert result['success'] is False


class TestPathTraversalSecurity:
    def test_read_path_traversal_blocked(self):
        result = json.loads(csv_process('read', '../../etc/passwd'))
        assert result['success'] is False
        assert 'validation failed' in result['error'].lower()

    def test_export_path_traversal_blocked(self):
        result = json.loads(csv_process('export', 'test.csv', output_path='../../evil.csv'))
        assert result['success'] is False

    def test_absolute_path_outside_working_dir_blocked(self):
        result = json.loads(csv_process('read', '/etc/passwd'))
        assert result['success'] is False


class TestSelectColumns:
    def test_select_specific_columns(self):
        rows = [{'name': 'Alice', 'age': '25', 'city': 'NYC'}]
        result = _select_columns(rows, ['name', 'age'])
        assert result == [{'name': 'Alice', 'age': '25'}]

    def test_select_no_columns_returns_all(self):
        rows = [{'name': 'Alice', 'age': '25'}]
        result = _select_columns(rows, None)
        assert result == rows


class TestFilterRows:
    def test_filter_greater_than(self):
        rows = [{'age': '25'}, {'age': '30'}, {'age': '35'}]
        result = _filter_rows(rows, 'age > 28')
        assert len(result) == 2

    def test_filter_equality(self):
        rows = [{'city': 'NYC'}, {'city': 'LA'}]
        result = _filter_rows(rows, "city == 'NYC'")
        assert len(result) == 1

    def test_filter_no_condition_returns_all(self):
        rows = [{'a': '1'}, {'a': '2'}]
        result = _filter_rows(rows, None)
        assert len(result) == 2


class TestAggregate:
    def test_aggregate_numeric_columns(self):
        rows = [{'age': '25'}, {'age': '30'}, {'age': '35'}]
        result = _aggregate(rows, ['age'])
        assert 'age' in result
        assert result['age']['sum'] == 90
        assert result['age']['avg'] == 30
        assert result['age']['min'] == 25
        assert result['age']['max'] == 35

    def test_aggregate_non_numeric_columns(self):
        rows = [{'name': 'Alice'}, {'name': 'Bob'}]
        result = _aggregate(rows, ['name'])
        assert 'name' in result
        assert result['name']['count'] == 2
        assert result['name']['unique'] == 2
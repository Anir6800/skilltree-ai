"""
Serializers for code execution API
"""

from rest_framework import serializers


class ExecuteCodeSerializer(serializers.Serializer):
    """Serializer for code execution request"""
    code = serializers.CharField(required=True, allow_blank=False)
    language = serializers.ChoiceField(
        choices=['python', 'javascript', 'cpp', 'java', 'go'],
        required=True
    )
    stdin = serializers.CharField(required=False, allow_blank=True, default="")


class TestCaseSerializer(serializers.Serializer):
    """Serializer for individual test case"""
    input = serializers.CharField(allow_blank=True, default="")
    expected = serializers.CharField(allow_blank=True, default="", required=False)
    expected_output = serializers.CharField(allow_blank=True, default="", required=False)
    
    def validate(self, data):
        # Accept either 'expected' or 'expected_output'
        if 'expected_output' in data and 'expected' not in data:
            data['expected'] = data['expected_output']
        elif 'expected' not in data and 'expected_output' not in data:
            data['expected'] = ""
        return data


class RunTestsSerializer(serializers.Serializer):
    """Serializer for running test cases"""
    code = serializers.CharField(required=True, allow_blank=False)
    language = serializers.ChoiceField(
        choices=['python', 'javascript', 'cpp', 'java', 'go'],
        required=True
    )
    test_cases = TestCaseSerializer(many=True, required=True)
    use_ai_simulation = serializers.BooleanField(required=False, default=False)

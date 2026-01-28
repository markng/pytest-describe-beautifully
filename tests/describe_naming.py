"""Tests for the naming module."""

from pytest_describe_beautifully.naming import (
    format_duration,
    humanize_describe_name,
    humanize_test_name,
)


def describe_humanize_describe_name():
    def it_strips_describe_prefix_from_camel_case():
        assert humanize_describe_name("describe_MyClass") == "MyClass"

    def it_strips_describe_prefix_from_snake_case():
        assert humanize_describe_name("describe_my_feature") == "my feature"

    def it_strips_Describe_prefix():
        assert humanize_describe_name("Describe_SomeClass") == "SomeClass"

    def it_handles_single_word_after_prefix():
        assert humanize_describe_name("describe_add") == "add"

    def it_returns_original_if_only_prefix():
        assert humanize_describe_name("describe_") == "describe_"

    def it_converts_underscores_if_no_prefix():
        assert humanize_describe_name("something_else") == "something else"

    def it_preserves_camel_case_with_multiple_words():
        assert humanize_describe_name("describe_MyClassMethod") == "MyClassMethod"

    def it_converts_multi_word_snake_case():
        assert humanize_describe_name("describe_my_cool_feature") == "my cool feature"

    def it_handles_uppercase_with_underscores():
        # Starts uppercase but has underscores → treated as snake_case
        assert humanize_describe_name("describe_My_Feature") == "My Feature"


def describe_humanize_test_name():
    def it_converts_it_prefix():
        assert humanize_test_name("it_does_something") == "it does something"

    def it_converts_they_prefix():
        assert humanize_test_name("they_are_equal") == "they are equal"

    def it_handles_single_word():
        assert humanize_test_name("it_works") == "it works"

    def it_handles_no_underscores():
        assert humanize_test_name("test") == "test"


def describe_format_duration():
    def it_formats_sub_millisecond():
        assert format_duration(0.0001) == "0ms"

    def it_formats_milliseconds():
        assert format_duration(0.123) == "123ms"

    def it_formats_sub_second():
        assert format_duration(0.999) == "999ms"

    def it_formats_exact_one_second():
        assert format_duration(1.0) == "1.00s"

    def it_formats_seconds():
        assert format_duration(2.5) == "2.50s"

    def it_formats_just_under_minute():
        assert format_duration(59.99) == "59.99s"

    def it_formats_exact_minute():
        assert format_duration(60.0) == "1m 0.0s"

    def it_formats_minutes_and_seconds():
        assert format_duration(125.0) == "2m 5.0s"

    def it_formats_large_duration():
        assert format_duration(3661.5) == "61m 1.5s"

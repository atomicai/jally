def convert_to_underscore(name):
    """
    'someFunctionWhateverMateYoLOLLel' -> 'some_Function_Whatever'

    >>> convert_to_underscore('test123isThisWorkingXXX')
    'test_123_is_This_Working_XXX'

    >>> convert_to_underscore('XXXNightmaremoonXXX')
    'XXXNightmaremoon_XXX'

    >>> convert_to_underscore('Hunter2')
    'Hunter_2'

    >>> convert_to_underscore('HDMI2GardenaGartenschlauchAdapter')
    'HDMI_2_Gardena_Gartenschlauch_Adapter'

    >>> convert_to_underscore('test23')
    'test_23'

    >>> convert_to_underscore('LEL24')
    'LEL_24'

    >>> convert_to_underscore('LittlepipIsBestPony11111')
    'Littlepip_Is_Best_Pony_11111'

    >>> convert_to_underscore('4458test')
    '4458_test'

    >>> convert_to_underscore('4458WUT')
    '4458_WUT'

    >>> convert_to_underscore('xXx4458xXx')
    'x_Xx_4458_x_Xx'

    >>> convert_to_underscore('XxX4458XxX')
    'Xx_X_4458_Xx_X'

    >>> convert_to_underscore('TestFoobarROfl')
    'Test_Foobar_ROfl'

    >>> convert_to_underscore('test_WoowFooBar')
    'test_Woow_Foo_Bar'
    """
    new_str = ""
    last_was_upper = None
    last_was_underscore = False
    last_was_number = None
    char: str
    for char in name:
        new_is_underscore = char == '_'
        new_is_upper = char.isupper()
        new_is_number = char.isdigit()
        if not last_was_upper is None:
            if last_was_upper == False and new_is_upper and not last_was_underscore:
                # swich from lower to upper case
                # but no underscore
                # 'aA' -> 'a_A'
                new_str += "_"
            elif last_was_number != new_is_number and not last_was_underscore:
                # switch from letter to number or other way around
                # but no underscore
                # 'a1' -> 'a_1'
                # 'A1' -> 'A_1'
                # '1A' -> '1_A'
                # '1a' -> '1_a'
                new_str += "_"
            # end if
        # end if
        last_was_underscore = new_is_underscore
        last_was_upper = new_is_upper
        last_was_number = new_is_number
        new_str += char
    # end for
    return new_str
# end def

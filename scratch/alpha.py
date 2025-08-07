def find_coordinates(number, total_columns):
    row = (number - 1) // total_columns + 1
    col = (number - 1) % total_columns + 1
    return row, col

# Example usage:
number = 9
total_columns = 5
row, col = find_coordinates(number, total_columns)
print(f"Coordinates of {number} are: ({row}, {col})")
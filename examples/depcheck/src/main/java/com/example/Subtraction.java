package com.example;

/**
 * A class dedicated to subtraction operations.
 */
public class Subtraction {

    /**
     * Subtracts two integers.
     * @param a The first integer (minuend).
     * @param b The second integer (subtrahend).
     * @return The difference of a and b.
     */
    public int subtract(int a, int b) {
        return a - b;
    }

    /**
     * Subtracts multiple integers from the first number.
     * @param first The first number to subtract from.
     * @param numbers The integers to subtract.
     * @return The result after subtracting all numbers from the first.
     */
    public int subtractMultiple(int first, int... numbers) {
        int result = first;
        for (int number : numbers) {
            result -= number;
        }
        return result;
    }
} 
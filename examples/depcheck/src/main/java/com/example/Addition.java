package com.example;

/**
 * A class dedicated to addition operations.
 */
public class Addition {

    /**
     * Adds two integers.
     * @param a The first integer.
     * @param b The second integer.
     * @return The sum of a and b.
     */
    public int add(int a, int b) {
        return a + b;
    }

    /**
     * Adds multiple integers.
     * @param numbers The integers to add.
     * @return The sum of all numbers.
     */
    public int addMultiple(int... numbers) {
        int sum = 0;
        for (int number : numbers) {
            sum += number;
        }
        return sum;
    }
} 
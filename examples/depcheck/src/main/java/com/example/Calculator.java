package com.example;

/**
 * A calculator class that uses separate Addition and Subtraction classes.
 */
public class Calculator {

    private final Addition addition;
    private final Subtraction subtraction;

    public Calculator() {
        this.addition = new Addition();
        this.subtraction = new Subtraction();
    }

    public Calculator(Addition addition, Subtraction subtraction) {
        this.addition = addition;
        this.subtraction = subtraction;
    }

    /**
     * Adds two integers using the Addition class.
     * @param a The first integer.
     * @param b The second integer.
     * @return The sum of a and b.
     */
    public int add(int a, int b) {
        return addition.add(a, b);
    }

    /**
     * Subtracts two integers using the Subtraction class.
     * @param a The first integer (minuend).
     * @param b The second integer (subtrahend).
     * @return The difference of a and b.
     */
    public int subtract(int a, int b) {
        return subtraction.subtract(a, b);
    }

    /**
     * Adds multiple integers using the Addition class.
     * @param numbers The integers to add.
     * @return The sum of all numbers.
     */
    public int addMultiple(int... numbers) {
        return addition.addMultiple(numbers);
    }

    /**
     * Subtracts multiple integers from the first number using the Subtraction class.
     * @param first The first number to subtract from.
     * @param numbers The integers to subtract.
     * @return The result after subtracting all numbers from the first.
     */
    public int subtractMultiple(int first, int... numbers) {
        return subtraction.subtractMultiple(first, numbers);
    }
}
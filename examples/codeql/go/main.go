package mygobuild

import (
	"fmt"
	"time"
)

// Greetter method with 5 params : name, place, age, fromDate, tillDate
func Greetter(name string, place string, age int, fromDate time.Time, tillDate time.Time) {
	fmt.Printf("Welcome %s , Please verify your details:\n", name)
	fmt.Printf("Place: %s\n", place)
	fmt.Printf("Age: %d\n", age)
	fmt.Printf("From Date: %s\n", fromDate.Format("2006-01-02"))
	fmt.Printf("Till Date: %s\n", tillDate.Format("2006-01-02"))
	fmt.Println("Thank you for providing your details!")
}

func main() {
	Greetter("John Doe", "New York", 30, time.Now().AddDate(0, 0, -7), time.Now())
}
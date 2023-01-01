---
published: true
---

Go/Golang is developed and supported by Google to obtain high-performance by having the static typing just like C, alongwith introducing simpler way for concurrent programming to achieve high bandwith throughput. As a result Golang became easier to grasp for a newcomer, and the standard libraries took care of basic http request-response model. More than 80% of codebase for Docker and kubernetes written in Go which popularized it, and Go became the de-facto choice for developing services and products on top of Docker and Kubernetes.

The main objective here is to provide an overview of Golang an snippet to understand the basics


#### Array

##### Example 01: Intro to Array
```go
package main

import ("fmt";"math/rand"; "time";"os")

func main2(){


	const(
		winter = 1
		summer = 3
		yearly = summer + winter
	)


	// var books [4]string
	
	books := [4]string{
		"book1",
		"book2",
		"book3",
	}

	// i := 4
	// books[i] = "asd"

	// books[4] = "asd"

	fmt.Printf("%T\n",books)
	fmt.Println(books);

	for i:=0;i<len(books);i++ {
		fmt.Println("Book element at index ",i,":",books[i])
	}

	fmt.Println("Unitialized string literal is empty string:", books[3]=="")
}
```

##### Example 02: Array with length determined at compile time
```go
// import "math/rand"

func main3(){
	moods := [...]string {"awesome","good","okayish","bad","terrible"}

	if len(os.Args) <2 {
		fmt.Println("[your name]")
		return
	}
	var name string = os.Args[1]
	rand.Seed(time.Now().UnixNano())
	var index int = rand.Intn(len(moods))
	fmt.Println(name," is currently feeling ",moods[index],"!")
}
```

##### Example 03: Array variable type checking includes the length also 
```go
func main4(){
	books1 := [4]string {"asd","asd","asd"}
	books2 := [4]string {"asd","asd","asd"}
	books3 := books1
	books4 := [4]string {"asd","asd","asd2"}
	books5 := [3]string {"asd","asd","asd2"}
	fmt.Println("Compare books1 & books2: ",books1==books2)
	fmt.Println("Compare books2 & books3: ",books2==books3)
	fmt.Println("Compare books1 & books4: ",books1==books4)
	// fmt.Println("Compare books1 & books5: ",books1==books5) // not compable: type is different.. compile time error

	fmt.Println(books5)
	// question: how to get type of variables?
}
```

##### Example 04: Array variable type checking includes type of array aling with length of array
```go
func main5(){
	books1 := [4]string {"book1","book2","book3"}
	books2 := books1
	books3 := [3]string {"book1","book2","book3"}

	books1[0] = "book_mod"
	fmt.Println("Books1 elements:",books1)
	fmt.Println("Books2 elements:",books2)
	fmt.Println("Books3 elements:",books3)

	// books2 = books3 // Type mismatch, hence assignment wont work here
}
```

##### Example 05: Iterations of array elements
```go
func main6(){
	array := [2][3] int{
		{1,2,3},
		{4,5},
	}

	for i:=0;i<len(array);i++{
		for j:=0;j<len(array[i]);j++ {
			fmt.Println("array at index ",i,",",j,": ",array[i][j])
		}
	}

	fmt.Println(array)
}
```

##### Example 06: Array type checking doesn't consider underlying type unless one of them is underlying type
```go
func main(){
	type booktype [3]int
	type cabinet [3]int
	books1 := booktype{3,4,5}
	books2 := [3]int {3,4,5}
	books3 := cabinet{3,4,5}

	fmt.Println("Compare books1 & books2: ",books1==books2)
	fmt.Println("Compare books3 & books2: ",books3==books2) // unnamed and named type comparision is resolved to underlying type
	// fmt.Println("Compare books1 & books3: ",books1==books3) // diff named types means different type, 
	fmt.Println("Compare books1 & books3: ",books1==booktype(books3))

	gadgets := [3]string{"Confused Drone"}
    fmt.Printf("%q\n", gadgets)
}

// consts are resolved compile time, no storage space allocated unlike variables
// check constants with iota
```

#### Function

##### Example 01: Basics of functions: Golang doesn't support method overloading
```go
package main

import "fmt"

func main(){
	fmt.Println("hello!")
	fmt.Println(fun1())
	fmt.Println("fun2() returns:", fun2())
	fmt.Println("fun3()  returns:", fun3(10))

	slice := []string{"hi!","there"}
	fmt.Println("slice: ",slice)
	fun4(slice)
	fmt.Println("slice: ",slice)

	array := [4]string{"hi!","there"}
	fmt.Println("array: ",array)
	fun5(array)
	fmt.Println("array: ",array)
}


func fun1() (string,string){
	// return "fun1 function" // always need to return same no. values declared
	return "fun1", "function"
}

// method overloading not supported in go
// func fun1(i int){

// }
```

##### Example 02: Named result value: Return mentions the return variable also: Return keyword implicitly declares, but needed
```go
func fun2() (m string){
	return // return is required even for named result value to be returned automatically
}
```

##### Example 03: Return
```go
func fun3(a int)(int){
	a++
	// return a++ //a++ means expecting expression
	return a
}
```

##### Example 04: Slice is a different data structure than array, which is why changes are reflected outside func4 but not in func5
```go
func fun4(slice []string){
	slice[0] = "hello"
}

func fun5(array [4]string){
	array[0] = "hello"
}
```

#### Slice: dynamic array


##### Example 01: Slice can be compared only to nil, unlike struct and array
```go
package main

import "fmt"

func main1(){
	var slice1 []int

	fmt.Println("slice1: ",slice1)

	var slice2 []int
	// fmt.Println("compare slice1 & slice2: ",slice1==slice2) //slice can only be compared to nil
	fmt.Println("Is slice1 empty: ",slice1==nil)
	fmt.Println("Length of slice2: ",len(slice2))

	slice3 := []string {"elem1","elem2","elem3"}
	fmt.Printf("Type of slice3: %T\n",slice3)
	fmt.Println("Length of slice3: ",len(slice3))
	fmt.Println("Is slice3 empty: ",slice3==nil)


	slice4 := append(slice3, "new_element")
	slice3[0] = "elem1_mod"
	fmt.Println("slice3 elements: ",slice3)
	fmt.Println("slice4 elements: ",slice4)

	// slice5 := append(slice3, slice4) // append cant append another slice, unpack slice to append all elements
	// fmt.Println("slice5 elemnets: ",slice5)
}
```

##### Example 02:
A slice is a descriptor of an array segment. It consists of a pointer to the array, the length of the segment, and its capacity (the maximum length of the segment).

```go
func main4(){
	// Slicing uses same backing array
	nums := []int {1,2,3,4,5,6,7,8,9,0}
	slice := nums[0:5]

	fmt.Printf("Type of nums: %T\n",nums)
	fmt.Println("nums elements:",nums)
	fmt.Println("slice elements:",slice)

	slice[0] = 11
	nums[4] = 44
	
	fmt.Println("nums elements:",nums)
	fmt.Println("slice elements:",slice)


	nums2 := [10]int {1,2,3,4,5,6}
	slice2 := nums2[0:5]
	fmt.Printf("Type of nums2: %T\n",nums2)
	fmt.Println("nums2 elements:",nums2)
	fmt.Println("slice2 elements:",slice2)

	slice2[0] = 11
	nums2[4] = 44
	
	fmt.Println("nums2 elements:",nums2)
	fmt.Println("slice2 elements:",slice2)

	// How to break this usage of same backing array? => bys using append
	var slice3 []int
	slice3 = append(slice3, nums[0:5]...)
	slice3[2] = 22
	fmt.Println("nums elements: ",nums)
	fmt.Println("slice3 elements: ",slice3)
}
```

##### Example 03: Runtime error 
```go
func main(){
	nums := []int{1,2,3,4,5,6,7}
	fmt.Println("nums elements:",nums)
	nums = nums[1:3]
	fmt.Println("nums elements:",nums)
	nums = nums[:6]
	fmt.Println("nums elements:",nums)
	// nums = nums[:7] // runtime error: out of range due to capcpity of slice
}
```


#### Struct

##### Example 01: Basics of struct
```go
package main

import "fmt"

func main1(){

	type person struct{
		firstname,lastname string
		age int
	}

	adam := person{
		firstname: "Adam",
		lastname: "mada",
		age: 10,
	}
	fmt.Println("Person struct: ",adam)
	fmt.Println("Person struct values: ",adam.firstname,adam.lastname,adam.age)

	adam.age = 20
	fmt.Println(adam)
}
```


##### Example 02: Structs are compable only if they're of same type

```go
func main(){

	type person struct {
		firstname, lastname string
		age int
	}

	pers1 := person{firstname:"perspn",lastname:"person",age:10}
	pers2 := person{firstname:"perspn",lastname:"person",age:10}
	pers3 := person{firstname:"perspn",lastname:"person",age:20}

	fmt.Println("Check equality pers1 & pers2: ",pers1==pers2)
	fmt.Println("Check equality pers1 & pers3: ",pers1==pers3)

	type book struct {
		name, author string
	}
	book1 := book{name:"name",author:"name"}

	fmt.Println(book1)
	// fmt.Println("Check equality: ",pers1==book1) // mismatched type

	type person2 struct {
		firstname, lastname string
		age int
	}
	pers4 := person2{firstname:"perspn",lastname:"person",age:20}
	fmt.Println(pers4)
	// fmt.Println("Check equality: ",pers3==pers4) // mismatched type

	var per6 person
	fmt.Println(per6)

	fmt.Printf("%T",per6)
}
```

#### OOP wrapper

```go
package main

import "fmt"

type book struct{
	name, author string
	price int
}

// Following is a function
func printBook(b book){
	fmt.Println("book details: ",b.name," author:",b.author," with price:",b.price)
}

// Following is a method: it's enticed to the type books
func (b *book) print(){
	fmt.Println("book details: ",b.name," author:",b.author," with price:",b.price)
	b.price = 200
}
// Use pointer reciever whenever value in large or need to update in the method

func main(){
	book1 := book{name:"book_name",author:"book_author",price:20}
	printBook(book1)
	book1.print()
	book1.print()

	(&book1).print()

	// print(book1) //NO: method is only accessible through type
	// book.print(book1)

	// var book2 book = nil
	// book2.print()
}

// Go doesn't have implements keyword: enticing interface methods would automatically statisfy interface criteria
// A type only statisfies interface when it's entricing all the interface methods
// type assertion: interface.(dynamic type)
// g,ok = p.(interface{discount(float64)}) 

// type switch: p.(type): case int/string/...

// interface of an interface?

// Go cant automatically take dynamic value's address from interface value: A non-pointer value is non-addressable, a copy

```

#### Doubt 01: Method receivers Value or pointer is implicitly decided

```go
package main

import "fmt"

func main() {
	fmt.Println("hello!")
	// doubt_function_pass()
	doubt_method_pointer_wopointer()
}

func doubt_function_pass() {
	book := Book{"book title", "book author"}
	fmt.Printf("Main: Address of book var: %p Value: %s\n", &book, book)
	checkPointer(&book)
	checkValue(book)
}

type Book struct {
	Title  string
	Author string
}

func checkPointer(book *Book) {
	fmt.Printf("checkPointer: Address of book var: %p Value: %s\n", book, *book)
}

func checkValue(book Book) {
	fmt.Printf("checkValue: Address of book var: %p Value: %s\n", &book, book)
}

func doubt_method_pointer_wopointer() {
	book := Book{"book title", "book author"}

	book1 := book
	fmt.Println("Following operations performed on struct value")
	book1.printBookDetailsValue()
	fmt.Println("book value: ", book1)
	book1.printBookDetailsPtr()
	fmt.Println("book value: ", book1)

	book2 := book
	fmt.Println("Following operations performed on struct pointer")
	book_ptr := &book2
	book_ptr.printBookDetailsValue()
	fmt.Println("book value: ", book2)
	book_ptr.printBookDetailsPtr()
	fmt.Println("book value: ", book2)
}

func (book Book) printBookDetailsValue() {
	book.Title = "book1"
	fmt.Printf("printBookDetailsValue: type: %T\n", book)
	fmt.Println("printBookDetailsValue: value:", book)
}

func (book *Book) printBookDetailsPtr() {
	book.Title = "book1"
	fmt.Printf("printBookDetailsPtr: type: %T\n", book)
	fmt.Println("printBookDetailsPtr: value:", book)
}
```




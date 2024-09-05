(define (factorial n)
  (if (= n 0)
      1
      (* n (factorial (- n 1)))))

; Simple expression with different types of data
( "hello world"
  5:abcde
  #68656c6c6f#  ; hexadecimal for "hello"
  |SGVsbG8gd29ybGQ=|  ; base64 for "Hello world"
  (inner-list "string in a list" 7:example)
)

; Another list with mixed content
( test-data
  (name "John Doe")
  (age 35)
  (base64-data |U29tZSByYW5kb20gZGF0YQ==|)
  (hex-data #48656c6c6f#)
  (sublist (item1 3:foo) (item2 3:bar))
)

; Empty list and nested list
( () (nested (1:1 2:22 3:333)) )

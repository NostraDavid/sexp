; Define factorial function
(define (factorial n)
  (if (= n 0)
      1
      (* n (factorial (- n 1)))))

; Define a function that computes the sum of a list
(define (sum-list lst)
  (if (null? lst)
      0
      (+ (car lst) (sum-list (cdr lst)))))

; Define a list of numbers
(define numbers (list 1 2 3 4 5))

; A nested list of symbols and strings
(define (nested-list)
  (list 'a 'b 'c "hello" "world" (list 'nested (list "deeper" "still deeper"))))

; Hexadecimal encoded string (representing "Hello" in hex)
(define (hex-example)
  #48656c6c6f#)

; Base64 encoded string (representing "Hello World")
(define (base64-example)
  |SGVsbG8gV29ybGQ=|)

; A simple quoted string
(define (quoted-example)
  "This is a quoted string with an escaped quote: \"inside\".")

; Complex expression with lists, quoted strings, and numbers
(define (complex-expression)
  (list "Item 1" 1234 (list "Nested" 'symbol "More" (list "Deeper" 5678))))

; A verbatim string with explicit length (8 characters)
(define (verbatim-string)
  8:verbatim)

; Define a simple mathematical function
(define (square x)
  (* x x))

; Define a map function to apply a function to each element in a list
(define (map func lst)
  (if (null? lst)
      '()
      (cons (func (car lst)) (map func (cdr lst)))))

; A list of various data types (numbers, symbols, strings, base64, hex)
(define mixed-list
  (list 42 "Answer to life" 'symbol |QmFzZTY0IGVuY29kZWQ=| #deadbeef#))

; Deeply nested S-expression for testing recursion
(define (deep-nesting)
  (list (list (list (list (list 'a 'b 'c))))))

; Example of a lambda function
(define (lambda-example)
  ((lambda (x) (* x x)) 5))

; Empty list
(define empty-list ())

; List with boolean values
(define (bool-list)
  (list #t #f #t))

; Predicate functions in S-expressions
(define (null-or-empty? lst)
  (or (null? lst) (empty? lst)))

(define (is-positive? n)
  (> n 0))

; Test mixed tokens
(list 'symbol-with-dash-and_underscore? 42)

; Quoted expressions in S-expressions
(define my-symbol 'symbol)
(define quoted-list '(1 2 3 4))

; Quoted expression example with nested list
'(a b c (d e))

; Hexadecimal and base64 that cannot be decoded to UTF-8
(define hex-example #deadbeef#)  ; Invalid UTF-8 sequence
(define base64-example |U29tZSByYW5kb20gZGF0YQ==|)  ; Decodable

; Invalid hexadecimal strings
(define hex-example ##)           ; Empty hex string

; Handle empty hexadecimal string
(define empty-hex ##)              ; Will return an empty byte sequence
(define valid-hex #deadbeef#)      ; Valid hex string

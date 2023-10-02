#include <iostream>

// Generate the list.hpp file with:
// interfacer -out:list.hpp list.yaml -guard:pragma
#include "list.hpp"

typedef unsigned int uint;

// NO INHERITANCE!
template<typename X, uint N>
struct StkArray {
	X data[N];

	X& at(int idx){
		return data[idx];
	}

	constexpr
	int len() const {
		return N;
	}
};

template<typename X>
struct HeapArray {
	X* data;
	uint length;

	X& at(int idx){
		return data[idx];
	}

	constexpr
	int len() const {
		return length;
	}

	HeapArray(uint n) : length{n} {
		data = new X[n];
		for(uint i = 0; i < n; i += 1){ data[i] = i; }
	}

	~HeapArray(){
		delete [] data;
	}
};

template<typename T>
void print_list(List<T> l){
	std::cout << "{" << l.len() << "} [ ";

	for(uint i = 0; i < l.len(); i += 1){
		std::cout << l.at(i) << ' ';
	}

	std::cout << "]\n";
}

int main(){
	auto heap  = HeapArray<float>(12);
	auto stack = StkArray<float, 3>{4,2,0};

	// l1 and l2 are "fat pointers", they have reference semantics
	auto l1 = make_list<float>(&heap);
	auto l2 = make_list<float>(&stack);

	print_list(l1);
	print_list(l2);

	l1.at(10) = 6;
	l2.at(0) = l1.at(10);

	l1.at(11) = 9;
	l2.at(1) = l1.at(11);

	print_list(l1);
	print_list(l2);

	return 0;
}

#include <iostream>

// Generate the list.hpp file with:
// interfacer -out:list.hpp list.yaml -guard:pragma
#include "list.hpp"
#include "allocator.hpp"

typedef unsigned int uint;

// NO INHERITANCE NEEDED!

struct HeapAllocator {
	void* alloc(usize nbytes){
		byte* p = (byte*)std::malloc(nbytes);
		if(p != nullptr){
			for(usize i = 0; i < nbytes; i += 1){
				p[i] = 0;
			}
		}
		return p;
	}

	void* alloc_undef(usize nbytes){
		byte* p = (byte*)std::malloc(nbytes);
		return p;
	}

	void* realloc(void* p, usize nbytes){
		return std::realloc(p, nbytes);
	}

	void free(void* p){
		std::free(p);
	}

	void free_all(){
		std::cerr << "Unsupported operation\n";
		std::abort();
	}

	bool has_address(void*){ return false; }

};

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
	Allocator alloc;

	X& at(int idx){
		return data[idx];
	}

	constexpr
	int len() const {
		return length;
	}

	HeapArray(Allocator al, uint n) : length{n}, alloc(al) {
		data = (float*)alloc.alloc(sizeof(X) * n);
		for(uint i = 0; i < n; i += 1){ data[i] = i; }
	}

	~HeapArray(){
		alloc.free(data);
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
	auto ally = HeapAllocator();

	auto heaparr  = HeapArray<float>(as_allocator(&ally), 12);
	auto stackarr = StkArray<float, 3>{4,2,0};

	// l1 and l2 are "fat pointers", they have reference semantics
	auto l1 = as_list<float>(&heaparr);
	auto l2 = as_list<float>(&stackarr);

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

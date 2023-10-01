#include <stdio.h>
#include "list.hpp"

template<typename T, int N>
struct Vec {
	T data[N];

	T& at(int idx) {
		return data[idx];
	}

	int len() const {
		return N;
	}
};

template<typename U>
struct Arr {
	U* data;
	int len_;

	U& at(int idx) {
		return data[idx];
	}

	int len() const {
		return len_;
	}
	Arr(int n){
		len_ = n;
		data = new U[n];
	}
	~Arr(){
		delete [] data;
	}
};

int main(){
	auto v = Vec<int, 8>{0};
	v.at(3) = 69;

	auto a = Arr<int>(8);
	a.at(2) = 420;

	auto vl = make_list<int>(&v);
	auto vl2 = make_list<int>(&v);

	printf("v[3] = %d\n", v.at(3));
	printf("v.len = %d\n", v.len());

	printf("a[2] = %d\n", a.at(2));
	printf("a.len = %d\n", a.len());

	vl2.at(3) = 100;
	printf("vl[3] = %d\n", vl.at(3));
	printf("vl[3] = %d\n", vl.at(3));
	printf("vl.len = %d\n", vl.len());
}

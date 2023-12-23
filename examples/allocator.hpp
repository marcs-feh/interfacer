/* Code generated by interfacer.py at 2023-12-23 16:38 */

#include <cstddef>
#include "types.hpp"

struct Allocator {
	struct VTable {
		void* (*alloc)(void * impl, usize nbytes);
		void* (*alloc_undef)(void * impl, usize nbytes);
		void* (*realloc)(void * impl, void* p, usize nbytes);
		void (*free)(void * impl, void* p);
		void (*free_all)(void * impl);
		bool (*has_address)(void * impl, void* p);
	};
	void * _impl;
	const VTable * _vtable;
	void* alloc(usize nbytes){
		return _vtable->alloc(_impl, nbytes);
	}
	void* alloc_undef(usize nbytes){
		return _vtable->alloc_undef(_impl, nbytes);
	}
	void* realloc(void* p, usize nbytes){
		return _vtable->realloc(_impl, p, nbytes);
	}
	void free(void* p){
		return _vtable->free(_impl, p);
	}
	void free_all(){
		return _vtable->free_all(_impl);
	}
	bool has_address(void* p){
		return _vtable->has_address(_impl, p);
	}
	template<typename _Impl>
	static constexpr
	VTable vtable_helper = {
		.alloc = [](void * impl, usize nbytes) -> void* {
			auto obj = reinterpret_cast<_Impl *>(impl);
			return obj->alloc(nbytes);
		},
		.alloc_undef = [](void * impl, usize nbytes) -> void* {
			auto obj = reinterpret_cast<_Impl *>(impl);
			return obj->alloc_undef(nbytes);
		},
		.realloc = [](void * impl, void* p, usize nbytes) -> void* {
			auto obj = reinterpret_cast<_Impl *>(impl);
			return obj->realloc(p, nbytes);
		},
		.free = [](void * impl, void* p) -> void {
			auto obj = reinterpret_cast<_Impl *>(impl);
			return obj->free(p);
		},
		.free_all = [](void * impl) -> void {
			auto obj = reinterpret_cast<_Impl *>(impl);
			return obj->free_all();
		},
		.has_address = [](void * impl, void* p) -> bool {
			auto obj = reinterpret_cast<_Impl *>(impl);
			return obj->has_address(p);
		}
	};
};
template<typename _Impl>
auto as_allocator(_Impl* impl){
	static constexpr const auto vt = Allocator::vtable_helper<_Impl>;
	return Allocator{
		._impl = impl,
		._vtable = &vt,
	};
}
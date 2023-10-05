#if __cplusplus >= 201703L
#define INTERFACER_CONSTEXPR constexpr
#else
#define INTERFACER_CONSTEXPR
#endif

using usize = int;

struct Allocator{
	struct VTable{
		void* (*alloc)(void * impl, usize nbytes);
		void* (*alloc_undef)(void * impl, usize nbytes);
		void (*free)(void * impl, void* ptr);
		void (*free_all)(void * impl);
		bool (*has_address)(void * impl, void* p);
	};

	void* impl = nullptr;
	const VTable *const vtbl = nullptr;

	void* alloc(usize nbytes){
		return vtbl->alloc(impl, nbytes);
	}
	void* alloc_undef(usize nbytes){
		return vtbl->alloc_undef(impl, nbytes);
	}
	void free(void* ptr){
		return vtbl->free(impl, ptr);
	}
	void free_all(){
		return vtbl->free_all(impl);
	}
	bool has_address(void* p){
		return vtbl->has_address(impl, p);
	}

	constexpr operator bool(){
		return (impl != nullptr) && (vtbl != nullptr);
	}
	template<typename Impl>
	static constexpr 
	VTable vtable_helper = {
		.alloc = [](void * impl, usize nbytes) -> void*{
			auto obj = reinterpret_cast< Impl*>(impl);
			return obj->alloc(nbytes);
		},
		.alloc_undef = [](void * impl, usize nbytes) -> void*{
			auto obj = reinterpret_cast< Impl*>(impl);
			return obj->alloc_undef(nbytes);
		},
		.free = [](void * impl, void* ptr) -> void{
			auto obj = reinterpret_cast< Impl*>(impl);
			return obj->free(ptr);
		},
		.free_all = [](void * impl) -> void{
			auto obj = reinterpret_cast< Impl*>(impl);
			return obj->free_all();
		},
		.has_address = [](void * impl, void* p) -> bool{
			auto obj = reinterpret_cast< Impl*>(impl);
			return obj->has_address(p);
		}
	};
};

template<typename Impl>
Allocator make_allocator(Impl* impl){
	static INTERFACER_CONSTEXPR const auto vt = Allocator::vtable_helper<Impl>;
	return Allocator{
		.impl = impl,
		.vtbl = &vt,
	};
}

/* IMPLEMENTATION
void* alloc(usize nbytes);
void* alloc_undef(usize nbytes);
void free(void* ptr);
void free_all();
bool has_address(void* p);
*/
#undef INTERFACER_CONSTEXPR

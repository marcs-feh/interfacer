struct Allocator{
    struct VTable{
        void* (*alloc)(void* impl, int nbytes);
        void* (*alloc_undef)(void* impl, int nbytes);
        void* (*realloc)(void* impl, void* ptr, int new_size);
        void (*free)(void* impl, void* ptr);
        void (*free_all)(void* impl);
        bool (*has_address)(void* impl, void* ptr);
    };

    const VTable *const vtbl = nullptr;
    void* impl = nullptr;

    void* alloc(void* impl, int nbytes){
        return vtbl->alloc(impl, nbytes);
    }
    void* alloc_undef(void* impl, int nbytes){
        return vtbl->alloc_undef(impl, nbytes);
    }
    void* realloc(void* impl, void* ptr, int new_size){
        return vtbl->realloc(impl, ptr, new_size);
    }
    void free(void* impl, void* ptr){
        return vtbl->free(impl, ptr);
    }
    void free_all(void* impl){
        return vtbl->free_all(impl);
    }
    bool has_address(void* impl, void* ptr){
        return vtbl->has_address(impl, ptr);
    }
Allocator(){
    tem
}
};
template<typename T>
constexpr Allocator::VTable Allocator_vtable = {
    .alloc = [](void* impl, int nbytes) -> void*{
        auto obj = reinterpret_cast<T*>(impl);
        return obj->alloc(nbytes);
    },
    .alloc_undef = [](void* impl, int nbytes) -> void*{
        auto obj = reinterpret_cast<T*>(impl);
        return obj->alloc_undef(nbytes);
    },
    .realloc = [](void* impl, void* ptr, int new_size) -> void*{
        auto obj = reinterpret_cast<T*>(impl);
        return obj->realloc(ptr, new_size);
    },
    .free = [](void* impl, void* ptr) -> void{
        auto obj = reinterpret_cast<T*>(impl);
        return obj->free(ptr);
    },
    .free_all = [](void* impl) -> void{
        auto obj = reinterpret_cast<T*>(impl);
        return obj->free_all();
    },
    .has_address = [](void* impl, void* ptr) -> bool{
        auto obj = reinterpret_cast<T*>(impl);
        return obj->has_address(ptr);
    }
};

template<typename T>
Allocator make_allocator(T* impl){
	constexpr auto vt = Allocator_vtable<T>;
	return Allocator{
		.impl = impl,
		.vtbl = &vt,
	};
}


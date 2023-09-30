template<typename T>
struct List{
    struct VTable{
        T& (*at)(void* impl, int idx);
        int (*len)(void* impl);
    };

    const VTable *const vtbl = nullptr;
    void* impl = nullptr;

    T& at(void* impl, int idx){
        return vtbl->at(impl, idx);
    }
    int len(void* impl){
        return vtbl->len(impl);
    }
};
template<typename T, typename Impl>
constexpr List<T>::VTable List_vtable = {
    .at = [](void* impl, int idx) -> T&{
        auto obj = reinterpret_cast<Impl*>(impl);
        return obj->at(idx);
    },
    .len = [](void* impl) -> int{
        auto obj = reinterpret_cast<Impl*>(impl);
        return obj->len();
    }
};

template<typename T, typename Impl>
List<T> make_list(Impl* impl){
	constexpr auto vt = List_vtable<T, Impl>;
	return List{
		.impl = impl,
		.vtbl = &vt,
	};
}

/* IMPLEMENTATION
T& at(int idx);
int len();
*/
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
};
template<typename Impl>
constexpr Allocator::VTable Allocator_vtable = {
    .alloc = [](void* impl, int nbytes) -> void*{
        auto obj = reinterpret_cast<Impl*>(impl);
        return obj->alloc(nbytes);
    },
    .alloc_undef = [](void* impl, int nbytes) -> void*{
        auto obj = reinterpret_cast<Impl*>(impl);
        return obj->alloc_undef(nbytes);
    },
    .realloc = [](void* impl, void* ptr, int new_size) -> void*{
        auto obj = reinterpret_cast<Impl*>(impl);
        return obj->realloc(ptr, new_size);
    },
    .free = [](void* impl, void* ptr) -> void{
        auto obj = reinterpret_cast<Impl*>(impl);
        return obj->free(ptr);
    },
    .free_all = [](void* impl) -> void{
        auto obj = reinterpret_cast<Impl*>(impl);
        return obj->free_all();
    },
    .has_address = [](void* impl, void* ptr) -> bool{
        auto obj = reinterpret_cast<Impl*>(impl);
        return obj->has_address(ptr);
    }
};

template<typename Impl>
Allocator make_allocator(Impl* impl){
	constexpr auto vt = Allocator_vtable<Impl>;
	return Allocator{
		.impl = impl,
		.vtbl = &vt,
	};
}

/* IMPLEMENTATION
void* alloc(int nbytes);
void* alloc_undef(int nbytes);
void* realloc(void* ptr, int new_size);
void free(void* ptr);
void free_all();
bool has_address(void* ptr);
*/

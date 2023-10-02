#pragma once

#if __cplusplus >= 201703L
#define INTERFACER_CONSTEXPR constexpr
#else
#define INTERFACER_CONSTEXPR
#endif

template<typename T>
struct List{
	struct VTable{
		T& (*at)(void * impl, int idx);
		int (*len)(void const* impl);
	};

	void* impl = nullptr;
	const VTable *const vtbl = nullptr;

	T& at(int idx){
		return vtbl->at(impl, idx);
	}
	int len() const {
		return vtbl->len(impl);
	}
};
template<typename T, typename Impl>
constexpr typename
List<T>::VTable List_vtable = {
	.at = [](void * impl, int idx) -> T&{
	    auto obj = reinterpret_cast< Impl*>(impl);
	    return obj->at(idx);
	},
	.len = [](void const* impl) -> int{
	    auto obj = reinterpret_cast<const Impl*>(impl);
	    return obj->len();
	}
};

template<typename T, typename Impl>
List<T> make_list(Impl* impl){
static constexpr const auto vt = List_vtable<T, Impl>;
	return List<T>{
		.impl = impl,
		.vtbl = &vt,
	};
}

/* IMPLEMENTATION
T& at(int idx);
int len()const;
*/
#undef INTERFACER_CONSTEXPR

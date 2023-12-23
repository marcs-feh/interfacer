template<typename T>
struct List {
struct VTable {
T& (*at)(void * impl, int idx);
int (*len)(const void * impl);
};
void * _impl;
const VTable * _vtable;
T& at(int idx){
return _vtable->at(_impl, idx);
}
int len() const {
return _vtable->len(_impl);
}
template<typename _Impl>
static constexpr
VTable vtable_helper = {
.at = [](void * impl, int idx) -> T& {
auto obj = reinterpret_cast<_Impl *>(impl);
return obj->at(idx);
},
.len = [](const void * impl) -> int {
auto obj = reinterpret_cast<const _Impl *>(impl);
return obj->len();
}
};
};
template<typename T, typename _Impl>
auto as_list(_Impl* impl){
static constexpr const auto vt = List<T>::template vtable_helper<_Impl>;
return List<T>{
._impl = impl,
._vtable = &vt,
};
}
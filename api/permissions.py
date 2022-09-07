form rest_framework import permissions


class IcreatorOrAdminReadOnly(permissions.BasePermission):
    edit_mmethods = ('PUT','PATCH')

    def has_object_permission(self,request, view, obj):
        
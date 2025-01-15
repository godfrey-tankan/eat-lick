from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Branch
from django.views.decorators.csrf import csrf_exempt

# Fetch branches (AJAX)
def get_branches(request):
    branches = Branch.objects.all().values('id', 'name', 'code')
    return JsonResponse({'branches': list(branches)})

def get_branch_details(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    return JsonResponse({'branch': {'id': branch.id, 'name': branch.name, 'code': branch.code}})

# Add new branch (AJAX)
@csrf_exempt
def add_branch(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        branch = Branch.objects.create(name=name, code=code)
        return JsonResponse({'message': 'Branch added successfully!', 'branch': {'id': branch.id, 'name': branch.name, 'code': branch.code}})

# Update branch (AJAX)
@csrf_exempt
def update_branch(request, branch_id):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        branch = Branch.objects.get(id=branch_id)
        branch.name = name
        branch.code = code
        branch.save()
        return JsonResponse({'message': 'Branch updated successfully!', 'branch': {'id': branch.id, 'name': branch.name, 'code': branch.code}})
    branch = get_object_or_404(Branch, id=branch_id)
    return JsonResponse({'branch': {'id': branch.id, 'name': branch.name, 'code': branch.code}})

# Delete branch (AJAX)
@csrf_exempt
def delete_branch(request, branch_id):
    if request.method == 'POST':
        branch = Branch.objects.get(id=branch_id)
        branch.delete()
        return JsonResponse({'message': 'Branch deleted successfully!'})

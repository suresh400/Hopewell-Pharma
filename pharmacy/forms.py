from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Medicine, Address, Review, Category


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    role = forms.ChoiceField(
        choices=[(role, label) for role, label in Profile.ROLE_CHOICES if role != 'DELIVERY_AGENT'],
        required=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'role', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all bg-white'})
        self.fields['email'].widget.attrs.update({'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all bg-white'})
        self.fields['phone'].widget.attrs.update({'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all bg-white'})
        self.fields['role'].widget.attrs.update({'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all bg-white'})
        self.fields['password1'].widget.attrs.update({'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all bg-white'})
        self.fields['password2'].widget.attrs.update({'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all bg-white'})


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
        }


class MedicineForm(forms.ModelForm):
    benefits_json = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter one benefit per line'}), required=False, help_text='Enter one benefit per line')
    how_to_use_json = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter one instruction per line'}), required=False, help_text='Enter one instruction per line')
    side_effects_json = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter one side effect per line'}), required=False, help_text='Enter one side effect per line')
    faqs_json = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Format: Question|Answer (one per line)'}), required=False, help_text='Format: Question|Answer (one per line)')
    additional_images_json = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter image URLs, one per line'}), required=False, help_text='Enter additional image URLs, one per line')
    
    class Meta:
        model = Medicine
        fields = [
            'category', 'supplier', 'sku', 'name', 'description',
            'mrp', 'price', 'gst_percent', 'stock', 'expiry_date',
            'prescription_required', 'image', 'image_url',
            'benefits_json', 'how_to_use_json', 'side_effects_json', 'faqs_json', 'additional_images_json'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'supplier': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'sku': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'rows': 4}),
            'mrp': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'gst_percent': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'expiry_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
            'prescription_required': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500'}),
            'image': forms.FileInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
        }
    
    def clean_benefits_json(self):
        data = self.cleaned_data.get('benefits_json', '')
        if data:
            return [line.strip() for line in data.split('\n') if line.strip()]
        return []
    
    def clean_how_to_use_json(self):
        data = self.cleaned_data.get('how_to_use_json', '')
        if data:
            return [line.strip() for line in data.split('\n') if line.strip()]
        return []
    
    def clean_side_effects_json(self):
        data = self.cleaned_data.get('side_effects_json', '')
        if data:
            return [line.strip() for line in data.split('\n') if line.strip()]
        return []
    
    def clean_faqs_json(self):
        data = self.cleaned_data.get('faqs_json', '')
        if data:
            faqs = []
            for line in data.split('\n'):
                if '|' in line:
                    q, a = line.split('|', 1)
                    faqs.append({'q': q.strip(), 'a': a.strip()})
            return faqs
        return []
    
    def clean_additional_images_json(self):
        data = self.cleaned_data.get('additional_images_json', '')
        if data:
            return [line.strip() for line in data.split('\n') if line.strip()]
        return []
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.benefits = self.cleaned_data.get('benefits_json', [])
        instance.how_to_use = self.cleaned_data.get('how_to_use_json', [])
        instance.side_effects = self.cleaned_data.get('side_effects_json', [])
        instance.faqs = self.cleaned_data.get('faqs_json', [])
        instance.additional_images = self.cleaned_data.get('additional_images_json', [])
        if commit:
            instance.save()
        return instance


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'street_address', 'city', 'state', 'pincode', 'landmark', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'street_address': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'state': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'pincode': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'landmark': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'feedback']
        widgets = {
            'rating': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'feedback': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'rows': 4}),
        }

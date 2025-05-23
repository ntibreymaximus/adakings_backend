from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):
    """Form for processing payments."""
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        self.step = kwargs.pop('step', 'select_method')  # Default to first step
        super().__init__(*args, **kwargs)
        
        # Set the order on the instance
        if self.order and not self.instance.order_id:
            self.instance.order = self.order
            
        # Set initial amount to order total if available
        if self.order and not self.initial.get('amount'):
            self.initial['amount'] = self.order.total_price
        
        # Set flag to skip mobile validation in first step
        if self.step == 'select_method':
            self.instance._skip_mobile_validation = True
    
    def clean(self):
        cleaned_data = super().clean()
        
        # If we're in the first step and selecting mobile money, don't validate mobile number yet
        if self.step == 'select_method' and cleaned_data.get('payment_method') == 'mobile_money':
            self.instance._skip_mobile_validation = True
        
        return cleaned_data
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        # Validate amount doesn't exceed order total
        if self.order and amount > self.order.total_price:
            raise forms.ValidationError(f"Payment amount (${amount}) cannot exceed order total (${self.order.total_price}).")
        
        return amount
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'amount', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class PaystackPaymentForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        help_text="Enter your mobile money number in the format: 024XXXXXXX or 054XXXXXXX",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 0241234567'})
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '')
        
        # Clean up the phone number format
        if phone.startswith('+'):
            # Remove the plus sign
            phone = phone[1:]
        
        # Ensure it's a Ghanaian number
        if phone.startswith('233'):
            # Already in international format
            pass
        elif phone.startswith('0'):
            # Convert to international format
            phone = '233' + phone[1:]
        else:
            raise forms.ValidationError("Please enter a valid Ghanaian phone number")
        
        return phone


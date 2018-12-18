from django import forms


class TrackerForm(forms.Form):
    url = forms.CharField(
        label='Event Page',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'https://www.residentadvisor.net/events/1234567'
        })
    )
    email = forms.EmailField(
        widget=forms.TextInput(attrs={'placeholder': 'john.doe@example.com'})
    )

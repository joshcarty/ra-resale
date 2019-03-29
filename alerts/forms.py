import re

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

    def clean_url(self):
        data = self.cleaned_data['url']
        pattern = r'https?:\/\/(?:www\.)?residentadvisor.net\/events\/\d+'
        match = re.search(pattern, data)
        if not match:
            raise forms.ValidationError("That doesn't look like an event page")
        return match.group(0)

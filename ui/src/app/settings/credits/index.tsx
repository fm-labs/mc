import { ContentSection } from '../components/content-section'
import { CreditsForm } from "@/app/settings/credits/credits-form.tsx";
import PaypalApp from "@/app/settings/paypal-app.tsx";

/**
 * SettingsCredits Component
 *
 * Settings component with a form to buy more token credits.
 * @constructor
 */
export function SettingsCredits() {
  return (
    <ContentSection
      title='Token Credits'
      desc='Buy more token credits to extend your usage of advanced features.'
    >
        <div>
            <h2 className='font-semibold text-lg mb-4'>Purchase Token Credits</h2>

            <p className='text-muted-foreground mt-2 mb-4'>
                After purchasing, your token credits will be automatically updated in your account.
                If you encounter any issues, please contact our support team.
            </p>

            <CreditsForm />

            <PaypalApp />
        </div>
    </ContentSection>
  )
}

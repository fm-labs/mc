import {ContentSection} from '../components/content-section'
import Header from "@/components/header.tsx";
import {Button} from "@/components/ui/button.tsx";
import ActiveSessions from "@/app/settings/security/active-sessions.tsx";
import {WebauthnRegister} from "@/app/settings/security/webauthn-register.tsx";
import {WebauthnLogin} from "@/app/settings/security/webauthn-login.tsx";

export function SettingsSecurity() {


    return (
        <ContentSection
            title='Security'
            desc='Manage your security settings, including password changes and
          two-factor authentication.'
        >
            <div className={"flex flex-col justify-center gap-8"}>
                <div>
                    <Header title={"Password & Security"}
                            subtitle={"Update your password and manage security settings."}/>
                    {/* Add your security settings form or components here */}
                    <div><Button>Change password</Button></div>
                </div>
                <div>
                    <Header title={"Pass Keys"}
                            subtitle={"Manage your passkeys here"}/>
                    {/* Add your security settings form or components here */}
                    <div><Button>Add pass key</Button></div>
                </div>
                <div>
                    <Header title={"Two-Factor Authentication"}
                            subtitle={"Manage 2FA settings"}/>
                    {/* Add your security settings form or components here */}
                    <div className={"flex flex-col gap-4"}>
                        <div><Button>Add Phone Number (verify via SMS code)</Button></div>
                        <div><Button>Add OTP (verify via Authenticator app)</Button></div>
                        <div><Button>Add Security Key (verify via Webauthn)</Button></div>
                    </div>

                    <WebauthnRegister />
                    <WebauthnLogin />
                </div>
                <div>
                    <Header title={"Active Sessions"}
                            subtitle={"View and manage your active sessions."}/>
                    {/* Add your security settings form or components here */}
                    <div>
                        <ActiveSessions/>
                    </div>
                </div>
            </div>
        </ContentSection>
    )
}

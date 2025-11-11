import React from 'react';
import Header from "@/components/header.tsx";

const AppLaunchPage = () => {
    return (
        <div>
            <Header title={"Launch Your Application"} />
            <main>
                <h1>Welcome to the App Launch Page</h1>
                <p>Here you can launch and manage your applications.</p>
            </main>
        </div>
    );
};

export default AppLaunchPage;
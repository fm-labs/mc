import logoJenkinsSvg from './logo-jenkins.svg';

export function IconJenkins({ className, ...props }: any) {
    return <img src={logoJenkinsSvg} alt="logo jenkins" className={className} {...props} />
}
